"""Frappe proxy endpoints for the Agent Factory box JSON API — generate & status.

Proxies behind CRM login + FF Ops/System Manager role, with X-Graph-Secret
attached server-side (shared helpers in ``_agent_box``):

  POST /agent-generate → generate(agent_id) — trigger Factory generate + verify
  GET  /agent-verify    → status(agent_id)   — check build/verify status

See: docs/specs/factory-reconciliation.md §4 (Box JSON API Contract)
"""

from __future__ import annotations

import json

import frappe
from werkzeug.wrappers import Response

from forsch_frontiers.api._agent_box import box_get, box_post, require_login_and_ops


@frappe.whitelist(methods=["POST"])
def generate(agent_id: str) -> Response:
    """Trigger Factory generate + verify. Proxies ``POST /agent-generate``."""
    require_login_and_ops()
    from urllib.parse import urlencode
    return box_post("/agent-generate", urlencode({"agent_id": agent_id}).encode())


@frappe.whitelist(methods=["GET"])
def status(agent_id: str) -> Response:
    """Check an agent's build/verify status. Proxies ``GET /agent-verify``."""
    require_login_and_ops()
    return box_get(f"/agent-verify?agent_id={agent_id}")
