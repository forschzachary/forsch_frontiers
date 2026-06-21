"""Reverse-proxy the read-only ADK Builder Cockpit behind CRM login.

The Cockpit runs on the cloud box, exposed publicly via Tailscale Funnel but
gated by a secret token (env ``COCKPIT_TOKEN``). This endpoint requires a
logged-in Frappe user, fetches the Cockpit server-side with the token, and
returns its HTML — so the token never reaches the browser and only
authenticated CRM users can view it.
"""

from __future__ import annotations

import os

import frappe
import requests
from werkzeug.wrappers import Response

COCKPIT_URL = "https://hubert-cloud-sp6.tail818cf8.ts.net:8443/"


@frappe.whitelist()
def embed():
    # @frappe.whitelist() already blocks guests, but be explicit.
    if frappe.session.user == "Guest":
        raise frappe.PermissionError("Login required")

    token = os.environ.get("COCKPIT_TOKEN") or ""
    last_exc = None
    for _ in range(3):  # Funnel can reset a cold connection; retry briefly.
        try:
            r = requests.get(COCKPIT_URL, params={"token": token}, timeout=25)
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
