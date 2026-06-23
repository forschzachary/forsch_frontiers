"""
FF Agent Task — controller hooks for YAML sync.
"""
import logging

import frappe
from frappe.model.document import Document

log = logging.getLogger("forsch_frontiers.sync")


class FFAgentTask(Document):
    def on_update(self):
        """Write tasks.yaml for the parent cluster on every save."""
        if not self.cluster:
            return
        try:
            from forsch_frontiers.sync.agent_graph import write_tasks
            write_tasks(self.cluster)
        except Exception:
            log.error("Failed to write YAML tasks for cluster %s", self.cluster, exc_info=True)

    def on_trash(self):
        """Clean up tasks.yaml when task is deleted."""
        if not self.cluster:
            return
        try:
            from forsch_frontiers.sync.agent_graph import write_tasks
            write_tasks(self.cluster)
        except Exception:
            log.error("Failed to clean YAML tasks for cluster %s", self.cluster, exc_info=True)
