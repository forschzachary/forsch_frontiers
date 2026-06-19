# Copyright (c) 2026, Zachary Forsch
import frappe
from frappe.model.document import Document


class FFNewsletterSubscription(Document):
    def validate(self):
        self._dedupe_pair()

    def _dedupe_pair(self):
        """One subscription per (crm_lead, audience). Quarantined rows (no lead)
        are exempt — many can share a blank lead while awaiting review."""
        if not self.crm_lead or not self.audience:
            return
        existing = frappe.db.get_value(
            "FF Newsletter Subscription",
            {
                "crm_lead": self.crm_lead,
                "audience": self.audience,
                "name": ["!=", self.name or ""],
            },
            "name",
        )
        if existing:
            frappe.throw(
                f"This lead is already subscribed to audience '{self.audience}' "
                f"({existing}). Update that record instead of creating a duplicate.",
                frappe.DuplicateEntryError,
            )
