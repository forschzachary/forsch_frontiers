"""Frappe-auth'd JSON proxy for agent generation + verification (box API).

Proxies POST /agent-generate and GET /agent-verify to the box. Follows the
graph_embed() pattern from cockpit.py: role-gated, X-Graph-Secret attached
server-side, JSON responses forwarded verbatim.

Contract: /opt/data/workspace/forsch_frontiers/docs/specs/factory-reconciliation.md §4
"""

from __future__ import annotations

import os

import frappe
import requests
from werkzeug.wrappers import Response

BOX_API_BASE = os.environ.get("BOX_API_BASE", "http://127.0.0.1:8780")
_GRAPH_SECRET = os.environ.get("GRAPH_SERVER_SECRET", "")


def _require_ops_role():
    """Raise PermissionError if user lacks System Manager or FF Ops role."""
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    roles = frappe.get_roles(frappe.session.user)
    if "System Manager" not in roles and "FF Ops" not in roles:
        raise frappe.PermissionError("FF Ops role required")


@frappe.whitelist(methods=["POST"])
def generate(agent_id: str):
    """Trigger Factory generate + verify for an agent.

    POST /agent-generate → box → JSON
    Mutating: requires FF Ops or System Manager role.
    """
    _require_ops_role()

    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    from urllib.parse import urlencode
    body = urlencode({"agent_id": agent_id}).encode()

    last_exc = None
    for _ in range(3):
        try:
            r = requests.post(
                BOX_API_BASE + "/agent-generate",
                headers={
                    "X-Graph-Secret": _GRAPH_SECRET,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=body,
                timeout=60,  # generate can take a while
            )
            return Response(r.content, status=r.status_code, mimetype="application/json")
        except requests.RequestException as exc:
            last_exc = exc

    return Response(
        f'{{"ok": false, "error": "box unreachable: {frappe.utils.escape_html(str(last_exc))}"}}'.encode(),
        status=502,
        mimetype="application/json",
    )


@frappe.whitelist(methods=["GET"])
def status(agent_id: str):
    """Check the verification status of an agent.

    GET /agent-verify?agent_id=<id> → box → JSON
    Read-only: any logged-in user.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    last_exc = None
    for _ in range(3):
        try:
            r = requests.get(
                BOX_API_BASE + f"/agent-verify?agent_id={agent_id}",
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
