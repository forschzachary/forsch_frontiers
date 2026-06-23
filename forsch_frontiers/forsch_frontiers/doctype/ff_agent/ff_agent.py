"""
FF Agent — controller hooks for YAML sync.
"""
import logging

import frappe
from frappe.model.document import Document

log = logging.getLogger("forsch_frontiers.sync")


class FFAgent(Document):
    def on_update(self):
        """Write registry/agents/agents.yaml on every save.

        YAML files are optional artifacts for the graph server's local fallback.
        The API reads from DB directly, so YAML write failures don't break anything.
        """
        try:
            from forsch_frontiers.sync.agent_graph import write_registry, write_shared
            write_registry()
            write_shared()
        except Exception:
            log.error("Failed to write YAML registry for agent %s", self.name, exc_info=True)

    def on_trash(self):
        """Clean up registry when agent is deleted."""
        try:
            from forsch_frontiers.sync.agent_graph import write_registry, write_shared
            write_registry()
            write_shared()
        except Exception:
            log.error("Failed to clean YAML registry for agent %s", self.name, exc_info=True)
