# Copyright (c) 2026, Zachary Forsch
import frappe
from frappe.model.document import Document


class FFAppRegistry(Document):
    def validate(self):
        self._normalize_slug()

    def _normalize_slug(self):
        """Slug must be URL-safe: lowercase, hyphens, no spaces."""
        if self.slug:
            self.slug = self.slug.strip().lower().replace(" ", "-")
