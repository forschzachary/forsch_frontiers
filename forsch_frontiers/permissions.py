"""Website permission hooks for forsch_frontiers."""

import frappe
from frappe.utils import get_url


def update_website_context(context):
    """Require login for agent-builder Web Page.

    The graph_embed endpoint already checks frappe.session.user != "Guest",
    but the Web Page itself was public — so unauthenticated users got a 200
    page shell with a 403 iframe. This hook redirects to login first, so the
    iframe always has a session cookie.

    context.login_required = True doesn't work here — that pattern only fires
    for doctypes that implement get_context() (like HelpArticle), not for
    generic Web Pages. We redirect directly instead.
    """
    if context.get("route") == "agent-builder" and frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = f"/login?redirect-to=/agent-builder"
        raise frappe.Redirect
