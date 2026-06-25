"""Frappe proxy endpoints for the Agent Factory box JSON API — config & tools.

Proxies the following box endpoints behind CRM login, with X-Graph-Secret
attached server-side (never exposed to the browser):

  GET  /agent-config   → get(agent_id)   — read full agent config
  GET  /agent-tools    → tools()         — list available ADK tools
  GET  /agent-models   → models(cluster) — list available LiteLLM models
  POST /agent-config   → save(...)       — save agent config + regenerate

All endpoints require the FF Ops or System Manager role.

See: docs/specs/factory-reconciliation.md §4 (Box JSON API Contract)
"""

from __future__ import annotations

import json
import os

import frappe
import requests
from werkzeug.wrappers import Response

# Box API base — Cloudflare tunnel in prod, localhost for dev.
BOX_API_BASE = os.environ.get("BOX_API_BASE", "http://127.0.0.1:8780")
_GRAPH_SECRET = os.environ.get("GRAPH_SERVER_SECRET", "")


def _require_ops_role():
    """Raise PermissionError unless user has FF Ops or System Manager role."""
    roles = frappe.get_roles(frappe.session.user)
    if "System Manager" not in roles and "FF Ops" not in roles:
        raise frappe.PermissionError("FF Ops or System Manager role required")


def _box_get(path: str) -> Response:
    """GET the box API with X-Graph-Secret, retry on cold tunnel, 502 on failure."""
    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    headers = {"X-Graph-Secret": _GRAPH_SECRET}

    last_exc = None
    for _ in range(3):  # Cold tunnel connection can reset; retry briefly.
        try:
            r = requests.get(BOX_API_BASE + path, headers=headers, timeout=30)
            return Response(
                r.content,
                status=r.status_code,
                mimetype=r.headers.get("content-type", "application/json"),
            )
        except requests.RequestException as exc:
            last_exc = exc

    msg = frappe.utils.escape_html(str(last_exc))
    return Response(
        json.dumps({"ok": False, "error": f"Box unreachable: {msg}"}).encode(),
        status=502,
        mimetype="application/json",
    )


def _box_post(path: str, body: str | bytes | None = None) -> Response:
    """POST the box API with X-Graph-Secret, retry on cold tunnel, 502 on failure."""
    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    headers = {
        "X-Graph-Secret": _GRAPH_SECRET,
        "Content-Type": "application/json",
    }

    last_exc = None
    for _ in range(3):  # Cold tunnel connection can reset; retry briefly.
        try:
            r = requests.post(
                BOX_API_BASE + path, headers=headers, data=body, timeout=30
            )
            return Response(
                r.content,
                status=r.status_code,
                mimetype=r.headers.get("content-type", "application/json"),
            )
        except requests.RequestException as exc:
            last_exc = exc

    msg = frappe.utils.escape_html(str(last_exc))
    return Response(
        json.dumps({"ok": False, "error": f"Box unreachable: {msg}"}).encode(),
        status=502,
        mimetype="application/json",
    )


# ── GET endpoints ─────────────────────────────────────────────────────


@frappe.whitelist(methods=["GET"])
def get(agent_id: str) -> Response:
    """Read an agent's full config from agents.yaml via the box API.

    Proxies to: ``GET /agent-config?agent_id=<agent_id>``
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    _require_ops_role()

    return _box_get(f"/agent-config?agent_id={agent_id}")


@frappe.whitelist(methods=["GET"])
def tools() -> Response:
    """List available ADK tools from the components library.

    Proxies to: ``GET /agent-tools``
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    _require_ops_role()

    return _box_get("/agent-tools")


@frappe.whitelist(methods=["GET"])
def models(cluster: str = "") -> Response:
    """List available LiteLLM models for a cluster.

    Proxies to: ``GET /agent-models?cluster=<cluster>``
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    _require_ops_role()

    path = f"/agent-models?cluster={cluster}" if cluster else "/agent-models"
    return _box_get(path)


# ── POST endpoints ────────────────────────────────────────────────────


@frappe.whitelist(methods=["POST"])
def save(
    agent_id: str,
    instruction: str | None = None,
    tools: str | None = None,
    model: str | None = None,
    group: str | None = None,
) -> Response:
    """Save an agent's config to agents.yaml + regenerate package.

    Proxies to: ``POST /agent-config``
    Body: JSON with agent_id and optional instruction / tools / model / group.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    _require_ops_role()

    payload: dict = {"agent_id": agent_id}
    if instruction is not None:
        payload["instruction"] = instruction
    if tools is not None:
        # Accept comma-separated string (from form) or leave as-is for JSON.
        payload["tools"] = tools
    if model is not None:
        payload["model"] = model
    if group is not None:
        payload["group"] = group

    return _box_post("/agent-config", json.dumps(payload).encode())
