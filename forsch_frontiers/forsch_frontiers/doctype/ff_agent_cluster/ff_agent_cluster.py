"""
FF Agent Cluster — controller hooks for YAML sync.
"""
import frappe
from frappe.model.document import Document


class FFAgentCluster(Document):
    def on_update(self):
        """Write cluster.yaml + project.md on every save."""
        from forsch_frontiers.sync.agent_graph import write_cluster, write_tasks, write_registry, write_shared
        write_cluster(self.cluster_id)
        write_tasks(self.cluster_id)
        write_registry()
        write_shared()

    def on_trash(self):
        """Clean up YAML files when cluster is deleted."""
        from pathlib import Path
        import frappe as _frappe
        from forsch_frontiers.sync.agent_graph import CLUSTERS_DIR, write_registry, write_shared
        cluster_dir = CLUSTERS_DIR / self.cluster_id
        if cluster_dir.exists():
            import shutil
            shutil.rmtree(cluster_dir)
        write_registry()
        write_shared()
