"""
FF Agent Task — controller hooks for YAML sync.
"""
import frappe
from frappe.model.document import Document


class FFAgentTask(Document):
    def on_update(self):
        """Write tasks.yaml for the parent cluster on every save."""
        from forsch_frontiers.sync.agent_graph import write_tasks
        write_tasks(self.cluster)

    def on_trash(self):
        """Clean up tasks.yaml when task is deleted."""
        from forsch_frontiers.sync.agent_graph import write_tasks
        write_tasks(self.cluster)
