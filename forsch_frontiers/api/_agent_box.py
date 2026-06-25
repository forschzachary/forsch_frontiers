"""Shared helpers for the Agent Factory box-API proxies.

Both ``agent_config.py`` and ``agent_factory.py`` reverse-proxy the box's
Agent Factory JSON API (routes added to the graph server's ``serve.py``),
attaching ``X-Graph-Secret`` server-side so it never reaches the browser.

The agent routes live in the SAME box server as the live-agent-graph, behind the
same Cloudflare tunnel — so we reuse ``GRAPH_BASE`` + ``GRAPH_SERVER_SECRET``
(the values ``cockpit.py`` already uses) rather than a separate base/secret.
``BOX_API_BASE`` overrides only if explicitly set.

See: docs/specs/factory-reconciliation.md §4 (Box JSON API Contract)
"""

from __future__ import annotations

import json
import os

import frappe
import requests
from werkzeug.wrappers import Response

# Reuse the graph tunnel + secret (agent routes are in the same serve.py).
BOX_API_BASE = (
    os.environ.get("BOX_API_BASE")
    or os.environ.get("GRAPH_BASE", "https://graph.forschfrontiers.com")
)
_GRAPH_SECRET = os.environ.get("GRAPH_SERVER_SECRET", "")


def require_login_and_ops():
    """Guard: logged-in user with FF Ops or System Manager role, else PermissionError."""
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    roles = frappe.get_roles(frappe.session.user)
    if "System Manager" not in roles and "FF Ops" not in roles:
        raise frappe.PermissionError("FF Ops or System Manager role required")


def _request(method: str, path: str, body: bytes | None = None) -> Response:
    """Proxy a request to the box API with the secret attached. Retries a cold
    tunnel briefly; returns a clean 502 on persistent failure."""
    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    headers = {"X-Graph-Secret": _GRAPH_SECRET}
    if method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    last_exc = None
    for _ in range(3):  # Cold tunnel connection can reset; retry briefly.
        try:
            r = requests.request(
                method, BOX_API_BASE + path, headers=headers, data=body, timeout=30
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


def box_get(path: str) -> Response:
    """GET the box API (read-only proxy)."""
    return _request("GET", path)


def box_post(path: str, body: bytes | None = None) -> Response:
    """POST the box API (mutating proxy)."""
    return _request("POST", path, body=body)
