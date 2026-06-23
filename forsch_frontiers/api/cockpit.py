"""Reverse-proxy the ADK Builder Cockpit and the Live Agent Graph behind CRM login.

The Cockpit runs on the cloud box, exposed publicly via Tailscale Funnel but
gated by a secret token (env ``COCKPIT_TOKEN``). ``embed`` requires a logged-in
Frappe user and forwards the request (any path + method + body) to the Cockpit
with the token attached server-side, returning the response verbatim. The token
never reaches the browser, and only authenticated CRM users can drive the tool.

The Graph server runs on the cloud box at ``127.0.0.1:8888``. ``graph_chat``
requires a logged-in Frappe user with the ``FF Ops`` role and forwards chat
messages to Hubert with a shared secret. The secret never reaches the browser,
and only authorized operators get a Hubert shell.
"""

from __future__ import annotations

import json
import os

import frappe
import requests
from werkzeug.wrappers import Response

COCKPIT_BASE = "https://hubert-cloud-sp6.tail818cf8.ts.net:8443"
GRAPH_BASE = "http://127.0.0.1:8888"
_ALLOWED_PREFIXES = ("/", "/api/")
_GRAPH_SECRET = os.environ.get("GRAPH_SERVER_SECRET", "")


@frappe.whitelist(methods=["GET", "POST"])
def embed(path: str = "/"):
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    if not path.startswith("/"):
        path = "/" + path
    if not any(path == p or path.startswith(p) for p in _ALLOWED_PREFIXES):
        raise frappe.PermissionError("Path not allowed")

    token = os.environ.get("COCKPIT_TOKEN") or ""
    method = (frappe.request.method or "GET").upper()
    body = frappe.request.get_data() if method == "POST" else None
    headers = {"X-Cockpit-Token": token}
    if method == "POST":
        headers["Content-Type"] = frappe.request.headers.get("Content-Type", "application/json")

    last_exc = None
    for _ in range(3):  # Funnel can reset a cold connection; retry briefly.
        try:
            r = requests.request(
                method,
                COCKPIT_BASE + path,
                params={"token": token},
                headers=headers,
                data=body,
                timeout=30,
            )
            ctype = r.headers.get("content-type", "text/html").split(";")[0]
            return Response(r.content, status=r.status_code, mimetype=ctype)
        except requests.RequestException as exc:
            last_exc = exc

    msg = frappe.utils.escape_html(str(last_exc))
    return Response(
        f"<h3>Cockpit unreachable</h3><pre>{msg}</pre>".encode(),
        status=502,
        mimetype="text/html",
    )


@frappe.whitelist(methods=["POST"])
def graph_chat(message: str, session_id: str | None = None):
    """Forward a chat message to Hubert on the graph server.

    Requires: logged-in user with FF Ops or System Manager role.
    The graph server is bound to 127.0.0.1 — only reachable from this box.
    Shared secret (GRAPH_SERVER_SECRET) authenticates the proxy to the server.
    """
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    roles = frappe.get_roles(frappe.session.user)
    if "System Manager" not in roles and "FF Ops" not in roles:
        raise frappe.PermissionError("FF Ops role required for Hubert chat")

    if not _GRAPH_SECRET:
        frappe.throw("GRAPH_SERVER_SECRET not configured on server")

    payload = {
        "message": message,
        "principal": frappe.session.user,
    }
    if session_id:
        payload["session_id"] = session_id

    try:
        r = requests.post(
            f"{GRAPH_BASE}/chat",
            json=payload,
            headers={
                "X-Graph-Secret": _GRAPH_SECRET,
                "Content-Type": "application/json",
            },
            timeout=120,
        )
        return r.json()
    except requests.RequestException as exc:
        return {"ok": False, "error": f"graph server unreachable: {exc}"}
