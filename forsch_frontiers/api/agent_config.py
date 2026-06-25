"""Frappe-auth'd JSON proxy for agent configuration (box API).

Proxies GET/POST to the box's /agent-config, /agent-tools, and /agent-models
endpoints. Follows the graph_embed() pattern from cockpit.py: role-gated,
X-Graph-Secret attached server-side, JSON responses forwarded verbatim.

Contract: /opt/data/workspace/forsch_frontiers/docs/specs/factory-reconciliation.md §4
"""

from __future__ import annotations

import os

import frappe
import requests
from werkzeug.wrappers import Response

BOX_API_BASE = os.environ.get("BOX_API_BASE", "http://127.0.0.1:8780")
_GRAPH_SECRET = os.environ.get("GRAPH_SERVER_SECRET", "")


def _proxy_get(path: str) -> Response:
    """Forward a GET to the box API with X-Graph-Secret, return JSON Response."""
    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    last_exc = None
    for _ in range(3):
        try:
            r = requests.get(
                BOX_API_BASE + path,
                headers={"X-Graph-Secret": _GRAPH_SECRET},
                timeout=30,
            )
            return Response(r.content, status=r.status_code, mimetype="application/json")
        except requests.RequestException as exc:
            last_exc = exc

    return Response(
        f'{{"ok": false, "error": "box unreachable: {frappe.utils.escape_html(str(last_exc))}"}}'.encode(),
        status=502,
        mimetype="application/json",
    )


def _proxy_post(path: str, data: bytes, content_type: str = "application/x-www-form-urlencoded") -> Response:
    """Forward a POST to the box API with X-Graph-Secret, return JSON Response."""
    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    last_exc = None
    for _ in range(3):
        try:
            r = requests.post(
                BOX_API_BASE + path,
                headers={
                    "X-Graph-Secret": _GRAPH_SECRET,
                    "Content-Type": content_type,
                },
                data=data,
                timeout=30,
            )
            return Response(r.content, status=r.status_code, mimetype="application/json")
        except requests.RequestException as exc:
            last_exc = exc

    return Response(
        f'{{"ok": false, "error": "box unreachable: {frappe.utils.escape_html(str(last_exc))}"}}'.encode(),
        status=502,
        mimetype="application/json",
    )


def _require_ops_role():
    """Raise PermissionError if user lacks System Manager or FF Ops role."""
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    roles = frappe.get_roles(frappe.session.user)
    if "System Manager" not in roles and "FF Ops" not in roles:
        raise frappe.PermissionError("FF Ops role required")


@frappe.whitelist(methods=["GET"])
def get(agent_id: str):
    """Read an agent's full config from the box.

    GET /agent-config?agent_id=<id> → box → JSON
    Read-only: any logged-in user.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    return _proxy_get(f"/agent-config?agent_id={agent_id}")


@frappe.whitelist(methods=["POST"])
def save(agent_id: str, instruction: str = "", tools: str = "", model: str = "", group: str = ""):
    """Save agent config to agents.yaml + regenerate package.

    POST /agent-config → box → JSON
    Mutating: requires FF Ops or System Manager role.
    """
    _require_ops_role()
    # Build form-encoded body matching what the box expects
    from urllib.parse import urlencode
    params = {"agent_id": agent_id}
    if instruction:
        params["instruction"] = instruction
    if tools:
        params["tools"] = tools
    if model:
        params["model"] = model
    if group:
        params["group"] = group
    body = urlencode(params).encode()
    return _proxy_post("/agent-config", body)


@frappe.whitelist(methods=["GET"])
def tools():
    """List available tools from the ADK components library.

    GET /agent-tools → box → JSON
    Read-only: any logged-in user.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    return _proxy_get("/agent-tools")


@frappe.whitelist(methods=["GET"])
def models():
    """List available models from LiteLLM proxy.

    GET /agent-models → box → JSON
    Read-only: any logged-in user.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    return _proxy_get("/agent-models")
