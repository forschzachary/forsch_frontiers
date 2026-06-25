"""Frappe proxy endpoints for the Agent Factory box JSON API — config & tools.

Proxies behind CRM login + FF Ops/System Manager role, with X-Graph-Secret
attached server-side (shared helpers in ``_agent_box``):

  GET  /agent-config   → get(agent_id)   — read full agent config
  GET  /agent-tools    → tools()         — list available ADK component tools
  GET  /agent-models   → models(cluster) — list available LiteLLM models
  POST /agent-config   → save(...)       — save agent config + regenerate

See: docs/specs/factory-reconciliation.md §4 (Box JSON API Contract)
"""

from __future__ import annotations

import json

import frappe
from werkzeug.wrappers import Response

from forsch_frontiers.api._agent_box import box_get, box_post, require_login_and_ops


@frappe.whitelist(methods=["GET"])
def get(agent_id: str) -> Response:
    """Read an agent's full config from agents.yaml. Proxies ``GET /agent-config``."""
    require_login_and_ops()
    return box_get(f"/agent-config?agent_id={agent_id}")


@frappe.whitelist(methods=["GET"])
def tools() -> Response:
    """List available ADK component tools (the toolbox). Proxies ``GET /agent-tools``."""
    require_login_and_ops()
    return box_get("/agent-tools")


@frappe.whitelist(methods=["GET"])
def models(cluster: str = "") -> Response:
    """List available LiteLLM models. Proxies ``GET /agent-models``."""
    require_login_and_ops()
    path = f"/agent-models?cluster={cluster}" if cluster else "/agent-models"
    return box_get(path)


@frappe.whitelist(methods=["POST"])
def save(
    agent_id: str,
    instruction: str | None = None,
    tools: str | None = None,
    model: str | None = None,
    group: str | None = None,
) -> Response:
    """Save an agent's config + regenerate. Proxies ``POST /agent-config``."""
    require_login_and_ops()
    payload: dict = {"agent_id": agent_id}
    if instruction is not None:
        payload["instruction"] = instruction
    if tools is not None:
        payload["tools"] = tools
    if model is not None:
        payload["model"] = model
    if group is not None:
        payload["group"] = group
    return box_post("/agent-config", json.dumps(payload).encode())
