"""App Ops API — log retrieval, health status, and model controls for the Apps cockpit.

Endpoints:
  /api/method/forsch_frontiers.api.app_ops.logs?slug=adk-bridge&lines=100
  /api/method/forsch_frontiers.api.app_ops.status?slug=adk-bridge
  /api/method/forsch_frontiers.api.app_ops.status_all
  /api/method/forsch_frontiers.api.app_ops.list_models
  /api/method/forsch_frontiers.api.app_ops.set_model  (POST: slug, model)
  /api/method/forsch_frontiers.api.app_ops.run_bench  (POST: cmd)
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time

import frappe
import requests


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_app(slug: str) -> dict:
    """Fetch an FF App Registry row by slug. Raises if missing."""
    app = frappe.db.get_value(
        "FF App Registry",
        slug,
        ["name", "app_name", "slug", "docker_container", "health_url",
         "url", "icon", "group", "status", "last_checked", "enabled",
         "model_override", "chainlit_port"],
        as_dict=True,
    )
    if not app:
        frappe.throw(f"No app registered with slug '{slug}'", frappe.DoesNotExistError)
    return app


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def logs(slug: str, lines: int = 100) -> dict:
    """Return the last N lines of Docker logs for an app.

    Requires the app to have a `docker_container` set. Runs `docker logs
    --tail N <container>` on the host machine. Returns `{slug, container,
    lines, output}`.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    app = _get_app(slug)
    container = app.docker_container
    if not container:
        frappe.throw(
            f"'{app.app_name}' has no Docker container configured. "
            "Set the Docker Container field in the app registry."
        )

    lines = min(max(int(lines), 1), 1000)  # clamp 1..1000

    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        frappe.throw("docker logs timed out (15s)", frappe.TimeoutError)
    except FileNotFoundError:
        frappe.throw("docker command not found on this host", frappe.ExecutionError)

    return {
        "slug": slug,
        "container": container,
        "lines": lines,
        "output": output[-50000:],  # cap at 50KB to avoid huge responses
    }


# ---------------------------------------------------------------------------
# Status (single app)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def status(slug: str) -> dict:
    """Check health of a single app and update the registry.

    If `health_url` is set, pings it (GET, 5s timeout). Otherwise marks
    status as 'unknown'. Returns `{slug, status, last_checked, latency_ms}`.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    app = _get_app(slug)
    health_url = app.health_url

    if not health_url:
        _update_status(slug, "unknown")
        return {"slug": slug, "status": "unknown", "last_checked": _now(), "latency_ms": None}

    start = time.monotonic()
    try:
        r = requests.get(health_url, timeout=5, allow_redirects=False)
        latency = int((time.monotonic() - start) * 1000)
        code = r.status_code

        if 200 <= code < 400:
            new_status = "live"
        elif code in (401, 403):
            new_status = "login"
        elif 400 <= code < 500:
            # 4xx (except auth) means the service is responding — just no content at root
            new_status = "live"
        else:
            new_status = "down"
    except requests.RequestException:
        latency = int((time.monotonic() - start) * 1000)
        new_status = "down"

    _update_status(slug, new_status)
    return {"slug": slug, "status": new_status, "last_checked": _now(), "latency_ms": latency}


# ---------------------------------------------------------------------------
# Status (all apps)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def status_all() -> list[dict]:
    """Ping every enabled app with a health_url and return results.

    Runs sequentially (not parallel) to avoid hammering the network.
    Updates each app's status in the registry. Returns a list of status dicts.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    apps = frappe.get_all(
        "FF App Registry",
        filters={"enabled": 1},
        fields=["slug", "health_url"],
    )

    results = []
    for app in apps:
        if not app.health_url:
            _update_status(app.slug, "unknown")
            results.append({"slug": app.slug, "status": "unknown", "latency_ms": None})
            continue

        start = time.monotonic()
        try:
            r = requests.get(app.health_url, timeout=5, allow_redirects=False)
            latency = int((time.monotonic() - start) * 1000)
            code = r.status_code

            if 200 <= code < 400:
                new_status = "live"
            elif code in (401, 403):
                new_status = "login"
            elif 400 <= code < 500:
                # 4xx (except auth) means the service is responding
                new_status = "live"
            else:
                new_status = "down"
        except requests.RequestException:
            latency = int((time.monotonic() - start) * 1000)
            new_status = "down"

        _update_status(app.slug, new_status)
        results.append({"slug": app.slug, "status": new_status, "latency_ms": latency})

    return results


# ---------------------------------------------------------------------------
# Model controls
# ---------------------------------------------------------------------------

@frappe.whitelist()
def list_models() -> list[dict]:
    """Fetch available models from the LiteLLM proxy.

    Returns a list of `{id, owned_by}` sorted by id. Reads the proxy URL
    and master key from environment variables LITELLM_BASE_URL and
    LITELLM_MASTER_KEY (set on the Frappe server).
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    base_url = os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000")
    master_key = os.environ.get("LITELLM_MASTER_KEY", "")

    if not master_key:
        frappe.throw("LITELLM_MASTER_KEY not configured on the server")

    try:
        r = requests.get(
            f"{base_url}/v1/models",
            headers={"Authorization": f"Bearer {master_key}"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
    except requests.RequestException:
        # Proxy unreachable — return hardcoded fallback (updated 2026-06-23)
        return _FALLBACK_MODELS

    models = [{"id": m["id"], "owned_by": m.get("owned_by", "")} for m in data]
    models.sort(key=lambda m: m["id"])
    return models


# Hardcoded fallback when LiteLLM proxy is unreachable from the Frappe server.
# Update this list when models change (add/remove in LiteLLM).
_FALLBACK_MODELS = [
    {"id": "cerebras-120b", "owned_by": ""},
    {"id": "deepseek-v4-flash", "owned_by": ""},
    {"id": "deepseek-v4-pro", "owned_by": ""},
    {"id": "gemini-2.5-flash", "owned_by": ""},
    {"id": "gemini-2.5-flash-aistudio", "owned_by": ""},
    {"id": "gemini-2.5-pro", "owned_by": ""},
    {"id": "gemini-3-flash-preview", "owned_by": ""},
    {"id": "gemini-3-pro-preview", "owned_by": ""},
    {"id": "gemma-4-12b-zachscpu", "owned_by": ""},
    {"id": "gemma4-31b", "owned_by": ""},
    {"id": "glm-5.1", "owned_by": ""},
    {"id": "glm-5.2", "owned_by": ""},
    {"id": "gpt-5.5", "owned_by": ""},
    {"id": "groq-compound", "owned_by": ""},
    {"id": "groq-gpt-oss-120b", "owned_by": ""},
    {"id": "groq-llama-70b", "owned_by": ""},
    {"id": "groq-qwen3-32b", "owned_by": ""},
    {"id": "groq-qwen3.6-27b", "owned_by": ""},
    {"id": "kimi-k2.6", "owned_by": ""},
    {"id": "kimi-k2.7-code", "owned_by": ""},
    {"id": "laguna-m.1", "owned_by": ""},
    {"id": "laguna-xs.2", "owned_by": ""},
    {"id": "mimo-v2-flash", "owned_by": ""},
    {"id": "mimo-v2.5", "owned_by": ""},
    {"id": "mimo-v2.5-pro", "owned_by": ""},
    {"id": "minimax-m2.7", "owned_by": ""},
    {"id": "minimax-m3", "owned_by": ""},
    {"id": "ministral-3b", "owned_by": ""},
    {"id": "nvidia-deepseek-v4-flash", "owned_by": ""},
    {"id": "nvidia-llama-70b", "owned_by": ""},
    {"id": "openrouter-nemotron-ultra-550b", "owned_by": ""},
    {"id": "qwen3-coder-480b", "owned_by": ""},
]


@frappe.whitelist(methods=["POST"])
def set_model(slug: str, model: str) -> dict:
    """Set the model override for an app.

    POST body: { "slug": "adk-bridge", "model": "mimo-v2.5" }
    Pass model="" to clear the override (revert to system default).
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    app = _get_app(slug)

    # Validate model exists in LiteLLM (if non-empty)
    if model:
        base_url = os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000")
        master_key = os.environ.get("LITELLM_MASTER_KEY", "")
        if master_key:
            try:
                r = requests.get(
                    f"{base_url}/v1/models",
                    headers={"Authorization": f"Bearer {master_key}"},
                    timeout=10,
                )
                r.raise_for_status()
                available = {m["id"] for m in r.json().get("data", [])}
                if model not in available:
                    frappe.throw(
                        f"Model '{model}' not found in LiteLLM. "
                        f"Available: {', '.join(sorted(available)[:10])}..."
                    )
            except requests.RequestException:
                pass  # If LiteLLM is unreachable, skip validation

    frappe.db.set_value("FF App Registry", slug, {"model_override": model or ""})
    frappe.db.commit()

    return {
        "slug": slug,
        "model_override": model or None,
        "app_name": app.app_name,
    }


# ---------------------------------------------------------------------------
# Bench bridge — run bench commands remotely
# ---------------------------------------------------------------------------

BENCH_PATH = os.environ.get("BENCH_PATH", "/home/frappe/frappe-bench")
BENCH_TIMEOUT = 120  # seconds


@frappe.whitelist(methods=["POST"])
def run_bench(bench_cmd: str, skip_site: bool = False) -> dict:
    """Run a bench command on the Railway server.

    POST body: { "bench_cmd": "migrate" } or { "bench_cmd": "restart", "skip_site": true }
    The --site flag is added automatically unless skip_site=true (for global
    commands like restart, clear-cache, etc. that don't accept --site).
    Returns {bench_cmd, stdout, stderr, code, bench_path}.

    Admin-only. This is a remote shell bridge — do not expose to untrusted users.
    """
    if frappe.session.user != "Administrator":
        raise frappe.PermissionError("Administrator only")

    if not bench_cmd or not bench_cmd.strip():
        frappe.throw("bench_cmd is required")

    bench_cmd = bench_cmd.strip()

    # Safety: block obviously dangerous commands
    _blocked = ["rm -rf", "drop ", "shutdown", "reboot", "init 0", "init 6"]
    cmd_lower = bench_cmd.lower()
    for bad in _blocked:
        if bad in cmd_lower:
            frappe.throw(f"Blocked dangerous command pattern: {bad}")

    site = frappe.local.site
    # No shell: split into an argv list so shell metacharacters (; && | `) cannot
    # inject. The denylist above is defense-in-depth only — the real boundary is
    # the Administrator gate (bench execute can still run Python; that is inherent
    # to bench, which is why this endpoint is admin-only and audited).
    try:
        extra = shlex.split(bench_cmd)
    except ValueError as e:
        frappe.throw(f"Could not parse bench_cmd: {e}")
    if skip_site:
        argv = ["bench", *extra]
    else:
        argv = ["bench", "--site", site, *extra]

    # Audit every invocation of this admin RCE bridge.
    frappe.logger("forsch_frontiers.run_bench").warning(
        "run_bench by %s: %s", frappe.session.user, bench_cmd
    )

    try:
        result = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=BENCH_TIMEOUT,
            cwd=BENCH_PATH,
        )
        stdout = result.stdout[-50000:] if result.stdout else ""
        stderr = result.stderr[-50000:] if result.stderr else ""
    except subprocess.TimeoutExpired:
        frappe.throw(f"Command timed out after {BENCH_TIMEOUT}s", frappe.TimeoutError)
    except Exception as e:
        frappe.throw(f"Failed to run command: {e}", frappe.ExecutionError)

    return {
        "cmd": bench_cmd,
        "argv": argv,
        "stdout": stdout,
        "stderr": stderr,
        "code": result.returncode,
        "bench_path": BENCH_PATH,
    }


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _update_status(slug: str, status: str) -> None:
    frappe.db.set_value("FF App Registry", slug, {
        "status": status,
        "last_checked": _now(),
    })
    frappe.db.commit()


def _now() -> str:
    return frappe.utils.now_datetime().isoformat()
