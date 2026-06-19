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
        meta = frappe.get_meta(dt)
        if not meta.has_field(link_field):
            continue
        filters = {link_field: anchor_name}
        # Never surface quarantined (unmatched) rows on the record — they're held
        # for human review, not served to the panel or to scoped agents.
        if meta.has_field("needs_review"):
            filters["needs_review"] = 0
        fields = ["name", "title", "status", "modified"]
        if meta.has_field("audience"):
            fields.append("audience")
        rows = frappe.get_all(
            dt,
            filters=filters,
            fields=fields,
            limit_page_length=50,
        )
        # Resolve the audience link to its display title for the panel.
        if meta.has_field("audience"):
            titles = dict(frappe.get_all("FF Audience", fields=["name", "title"], as_list=True))
            for r in rows:
                if r.get("audience"):
                    r["audience_title"] = titles.get(r["audience"], r["audience"])
        out[key] = rows
    return out
