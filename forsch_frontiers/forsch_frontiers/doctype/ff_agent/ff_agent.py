"""
FF Agent — controller hooks for YAML sync.
"""
import frappe
from frappe.model.document import Document


class FFAgent(Document):
    def on_update(self):
        """Write registry/agents/agents.yaml on every save."""
        from forsch_frontiers.sync.agent_graph import write_registry, write_shared
        write_registry()
        write_shared()

    def on_trash(self):
        """Clean up registry when agent is deleted."""
        from forsch_frontiers.sync.agent_graph import write_registry, write_shared
        write_registry()
        write_shared()
