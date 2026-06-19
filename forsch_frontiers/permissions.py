# Forsch Frontiers — row-level permission query conditions.
import frappe


def subscription_query_conditions(user=None):
    """Append a WHERE condition that hides quarantined (needs_review) subscriptions
    from every role except System Manager / Administrator.

    This is defense beyond the parity API: even a direct
    `/api/resource/FF Newsletter Subscription` query from a scoped key cannot see
    unmatched rows. Frappe appends the returned string to the query's WHERE clause.
    """
    user = user or frappe.session.user
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return ""
    return "`tabFF Newsletter Subscription`.needs_review = 0"
