"""Reverse-proxy the ADK Builder Cockpit behind CRM login.

The Cockpit runs on the cloud box, exposed publicly via Tailscale Funnel but
gated by a secret token (env ``COCKPIT_TOKEN``). ``embed`` requires a logged-in
Frappe user and forwards the request (any path + method + body) to the Cockpit
with the token attached server-side, returning the response verbatim. The token
never reaches the browser, and only authenticated CRM users can drive the tool.
"""

from __future__ import annotations

import os

import frappe
import requests
from werkzeug.wrappers import Response

COCKPIT_BASE = "https://hubert-cloud-sp6.tail818cf8.ts.net:8443"
_ALLOWED_PREFIXES = ("/", "/api/")


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
