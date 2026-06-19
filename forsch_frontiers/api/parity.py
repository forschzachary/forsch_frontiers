# Forsch Frontiers — agent/UI-facing read API (promoted from spike 001).
import frappe

# FF object key -> DocType. Extended as DocTypes land in later slices.
FF_DOCTYPES = {
    "newsletterSubscription": "FF Newsletter Subscription",
}


@frappe.whitelist()
def related_records(anchor_doctype, anchor_name):
    """Return Forsch custom records linked to a CRM Lead or Contact."""
    if anchor_doctype not in ("CRM Lead", "Contact"):
        frappe.throw("Unsupported anchor doctype")
    link_field = "crm_lead" if anchor_doctype == "CRM Lead" else "contact"
    out = {}
    for key, dt in FF_DOCTYPES.items():
        if not frappe.db.exists("DocType", dt):
            continue
        if not frappe.get_meta(dt).has_field(link_field):
            continue
        out[key] = frappe.get_all(
            dt,
            filters={link_field: anchor_name},
            fields=["name", "title", "status", "modified"],
            limit_page_length=50,
        )
    return out
