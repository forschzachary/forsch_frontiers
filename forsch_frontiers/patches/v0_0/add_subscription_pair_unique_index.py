import frappe


def execute():
    """Hard DB guarantee: one FF Newsletter Subscription per (crm_lead, audience).

    The controller validate() gives a friendly error; this index makes the
    invariant impossible to violate even via direct writes. NULL crm_lead
    (quarantined rows) repeats freely — MySQL unique indexes treat NULLs as
    distinct, so many unmatched rows can coexist.
    """
    table = "tabFF Newsletter Subscription"
    index_name = "ff_sub_lead_audience_ux"
    if frappe.db.has_index(table, index_name):
        return
    frappe.db.add_unique(
        "FF Newsletter Subscription",
        ["crm_lead", "audience"],
        constraint_name=index_name,
    )
