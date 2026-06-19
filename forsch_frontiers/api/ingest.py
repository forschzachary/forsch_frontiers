# Forsch Frontiers — ingest helpers. The single source of truth for clean,
# deduped, leak-safe data coming into the FF lanes (used by seed now + the
# listmonk back-sync in Slice 2b).
import frappe


def normalize_email(email):
    """Lowercase + strip. ALL email matching goes through here so casing/whitespace
    can never split one person into two."""
    if not email:
        return None
    return email.strip().lower() or None


def match_lead_by_email(email):
    """Resolve a (normalized) email to a CRM Lead name, or None if no clean match.

    - No email / no match -> None (caller quarantines: needs_review=1, blank crm_lead).
    - Multiple leads share the email -> oldest lead wins, ambiguity logged.
    """
    norm = normalize_email(email)
    if not norm:
        return None
    candidates = frappe.get_all(
        "CRM Lead",
        filters={"email": ["like", f"%{norm}%"]},
        fields=["name", "email", "creation"],
        order_by="creation asc",
    )
    matches = [c for c in candidates if normalize_email(c.get("email")) == norm]
    if not matches:
        return None
    if len(matches) > 1:
        frappe.logger("ff-ingest").warning(
            f"{len(matches)} CRM Leads match {norm}; using oldest {matches[0]['name']}"
        )
    return matches[0]["name"]
