"""Frappe proxy endpoints for the Agent Factory box JSON API — generate & status.

Proxies the following box endpoints behind CRM login, with X-Graph-Secret
attached server-side (never exposed to the browser):

  POST /agent-generate → generate(agent_id) — trigger Factory generation
  GET  /agent-verify    → status(agent_id)   — check verification status

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


# ── POST endpoints ────────────────────────────────────────────────────


@frappe.whitelist(methods=["POST"])
def generate(agent_id: str) -> Response:
    """Trigger Factory generation + verify for an agent.

    Proxies to: ``POST /agent-generate``
    Body: JSON ``{"agent_id": "<id>"}``
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    _require_ops_role()

    payload = json.dumps({"agent_id": agent_id}).encode()
    return _box_post("/agent-generate", payload)


# ── GET endpoints ─────────────────────────────────────────────────────


@frappe.whitelist(methods=["GET"])
def status(agent_id: str) -> Response:
    """Check the verification / build status of an agent.

    Proxies to: ``GET /agent-verify?agent_id=<agent_id>``
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")
    _require_ops_role()

    return _box_get(f"/agent-verify?agent_id={agent_id}")
