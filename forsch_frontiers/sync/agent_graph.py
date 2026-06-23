"""
Agent Graph Sync — bidirectional bridge between CRM DocTypes and YAML files.

CRM (Frappe DB)  ←→  YAML (forsch_frontiers repo)  ←→  live-agent-graph (manifest)

Flow:
  1. User edits FF Agent / FF Agent Cluster / FF Agent Task in CRM Desk
  2. Controller on_update hook calls sync.write_*()
  3. YAML files are written to the forsch_frontiers app directory
  4. Git commit + push (optional, configurable)
  5. Cloud box pulls → live-agent-graph rebuilds manifest → graph UI updates

Reverse flow (CRM reads YAML):
  1. Whitelisted API endpoint reads YAML files
  2. Returns structured data for the graph server
"""

import os
from pathlib import Path

import frappe
import yaml

# Where YAML files live inside the forsch_frontiers app
# On Railway, this is /home/frappe/frappe-bench/apps/forsch_frontiers/forsch_frontiers/
# We use frappe.get_app_path() to resolve it correctly
APP_DIR = Path(frappe.get_app_path("forsch_frontiers"))
AGENT_GRAPH_DIR = APP_DIR / "agent_graph"
REGISTRY_DIR = AGENT_GRAPH_DIR / "registry" / "agents"
CLUSTERS_DIR = AGENT_GRAPH_DIR / "clusters"
SHARED_DIR = AGENT_GRAPH_DIR / "shared"


def ensure_dirs():
    """Create the agent_graph directory tree if it doesn't exist."""
    for d in [REGISTRY_DIR, CLUSTERS_DIR, SHARED_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def write_registry():
    """Write registry/agents/agents.yaml from all FF Agent docs."""
    ensure_dirs()
    agents = frappe.get_all(
        "FF Agent",
        fields=["agent_id", "title", "description", "purpose", "model",
                "safety_level", "role", "group", "status"],
    )
    registry = {
        "version": 1,
        "defaults": {
            "agent_class": "LlmAgent",
        },
        "agents": {},
    }
    for a in agents:
        aid = a["agent_id"]
        # Fetch child table rows
        tools = frappe.get_all(
            "FF Agent Tool",
            filters={"parent": aid},
            fields=["tool_name"],
            pluck="tool_name",
        )
        channels = frappe.get_all(
            "FF Agent Channel",
            filters={"parent": aid},
            fields=["channel_name"],
            pluck="channel_name",
        )
        registry["agents"][aid] = {
            "description": a.get("description") or "",
            "discord_channels": channels or [],
            "safety_level": a.get("safety_level") or "read_only",
            "purpose": a.get("purpose") or "",
            "tools": tools or [],
            "model": a.get("model") or "",
            "role": a.get("role") or "plain",
        }
        if a.get("group"):
            registry["agents"][aid]["group"] = a["group"]

    yaml_path = REGISTRY_DIR / "agents.yaml"
    yaml_path.write_text(yaml.dump(registry, default_flow_style=False, sort_keys=False, allow_unicode=True))
    return str(yaml_path)


def write_cluster(cluster_id: str):
    """Write clusters/<cluster_id>/cluster.yaml + project.md from FF Agent Cluster doc."""
    ensure_dirs()
    doc = frappe.get_doc("FF Agent Cluster", cluster_id)
    cluster_dir = CLUSTERS_DIR / cluster_id
    cluster_dir.mkdir(parents=True, exist_ok=True)

    # cluster.yaml
    members = [m.agent for m in doc.members]
    connectors = [c.connector_name for c in doc.data_connectors]
    cluster_yaml = {
        "name": doc.cluster_id,
        "description": doc.goal or "",
        "members": members,
        "config": {
            "default_model": doc.default_model or "gpt-5.5",
        },
        "routing": {
            "max_delegation_depth": doc.max_delegation_depth or 3,
        },
    }
    (cluster_dir / "cluster.yaml").write_text(
        f"# {doc.cluster_id} cluster\n"
        + yaml.dump(cluster_yaml, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )

    # project.md
    status = doc.status or "blank"
    handoff = doc.handoff_pct or 0
    goal = doc.goal or ""
    project_md = f"""---
goal: "{goal}"
status: {status}
handoff_pct: {handoff}
data_connectors:
"""
    for c in connectors:
        project_md += f"  - {c}\n"
    project_md += f"---\n# {doc.cluster_id}\n\n{doc.goal or 'New cluster.'}\n"
    (cluster_dir / "project.md").write_text(project_md)

    return str(cluster_dir)


def write_tasks(cluster_id: str):
    """Write clusters/<cluster_id>/tasks.yaml from FF Agent Task docs."""
    ensure_dirs()
    tasks = frappe.get_all(
        "FF Agent Task",
        filters={"cluster": cluster_id},
        fields=["name", "title", "agent", "depth", "gp_project", "gp_task"],
    )
    cluster_dir = CLUSTERS_DIR / cluster_id
    cluster_dir.mkdir(parents=True, exist_ok=True)

    task_list = []
    for t in tasks:
        chain_rows = frappe.get_all(
            "FF Task Chain Agent",
            filters={"parent": t["name"]},
            fields=["agent", "order"],
            order_by="order",
        )
        chain = [c["agent"] for c in chain_rows]
        task_list.append({
            "id": t["name"],
            "title": t.get("title") or "",
            "agent_id": t.get("agent") or "",
            "cluster_id": cluster_id,
            "parent": t.get("gp_task") or None,
            "chain": chain,
            "depth": t.get("depth") or len(chain),
        })

    tasks_yaml = {"tasks": task_list}
    (cluster_dir / "tasks.yaml").write_text(
        yaml.dump(tasks_yaml, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )
    return str(cluster_dir / "tasks.yaml")


def write_shared():
    """Write shared/components.yaml from the registry tools/models."""
    ensure_dirs()
    agents = frappe.get_all("FF Agent", fields=["agent_id"])
    all_tools = set()
    all_models = set()
    for a in agents:
        tools = frappe.get_all(
            "FF Agent Tool",
            filters={"parent": a["agent_id"]},
            fields=["tool_name"],
            pluck="tool_name",
        )
        all_tools.update(tools)
        model = frappe.get_value("FF Agent", a["agent_id"], "model")
        if model:
            all_models.add(model)

    shared = {
        "tools": sorted(all_tools),
        "models": sorted(all_models),
        "connections": {
            "github": "GitHub (OAuth)",
            "resend": "Resend (email)",
            "cloudflare-global": "Cloudflare (global)",
            "frappe-crm": "Frappe CRM (ff-ops-prod)",
        },
        "tool_connections": {
            "get_crm_health_snapshot": "frappe-crm",
            "list_recent_crm_leads": "frappe-crm",
        },
    }
    (SHARED_DIR / "components.yaml").write_text(
        "# Shared Components — tools, models, and infrastructure common to all clusters\n"
        + yaml.dump(shared, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )
    return str(SHARED_DIR / "components.yaml")


def write_all():
    """Full sync: write registry, all clusters, and shared components."""
    ensure_dirs()
    results = []
    results.append(("registry", write_registry()))
    clusters = frappe.get_all("FF Agent Cluster", pluck="cluster_id")
    for cid in clusters:
        results.append((f"cluster:{cid}", write_cluster(cid)))
        results.append((f"tasks:{cid}", write_tasks(cid)))
    results.append(("shared", write_shared()))
    return results


# ── Whitelisted API endpoints ──

@frappe.whitelist(methods=["GET"])
def get_agent_graph_manifest(cluster_id: str):
    """Return the full agent graph manifest for a cluster (reads YAML, not DB)."""
    ensure_dirs()
    cluster_dir = CLUSTERS_DIR / cluster_id
    if not cluster_dir.exists():
        frappe.throw(f"Cluster '{cluster_id}' not found", frappe.DoesNotExistError)

    # Read YAML files
    registry_yaml = REGISTRY_DIR / "agents.yaml"
    shared_yaml = SHARED_DIR / "components.yaml"
    cluster_yaml = cluster_dir / "cluster.yaml"

    registry = yaml.safe_load(registry_yaml.read_text()) if registry_yaml.exists() else {}
    shared = yaml.safe_load(shared_yaml.read_text()) if shared_yaml.exists() else {}
    cluster_def = yaml.safe_load(cluster_yaml.read_text()) if cluster_yaml.exists() else {}

    agents = registry.get("agents", {})
    member_ids = cluster_def.get("members", [])
    cluster_agents = {aid: agents[aid] for aid in member_ids if aid in agents}

    return {
        "cluster": cluster_id,
        "agents": cluster_agents,
        "shared": shared,
        "cluster_config": cluster_def,
    }


@frappe.whitelist(methods=["GET"])
def list_clusters():
    """Return all clusters with their project.md front-matter."""
    ensure_dirs()
    result = []
    if not CLUSTERS_DIR.exists():
        return result
    for d in sorted(CLUSTERS_DIR.iterdir()):
        if not d.is_dir():
            continue
        cluster_yaml = d / "cluster.yaml"
        project_md = d / "project.md"
        if not cluster_yaml.exists():
            continue
        entry = {"name": d.name}
        if project_md.exists():
            text = project_md.read_text()
            if text.startswith("---"):
                end = text.find("---", 3)
                if end > 0:
                    fm = yaml.safe_load(text[3:end]) or {}
                    entry["goal"] = fm.get("goal", "")
                    entry["status"] = fm.get("status", "")
                    entry["handoff_pct"] = fm.get("handoff_pct", 0)
        result.append(entry)
    return result


@frappe.whitelist(methods=["POST"])
def sync_all():
    """Trigger a full sync: CRM -> YAML. Called after bulk changes or on demand."""
    results = write_all()
    return {"ok": True, "files": [{"type": t, "path": p} for t, p in results]}
# ── Bidirectional GP Task <-> FF Agent Task sync ──

def _sync_gp_to_agent_task(doc, method):
    """doc_events hook: when GP Task is created/updated, sync to FF Agent Task."""
    if frappe.flags.in_sync_agent_task:
        return
    frappe.flags.in_sync_agent_task = True
    try:
        # Find existing FF Agent Task linked to this GP Task
        existing = frappe.get_all(
            "FF Agent Task",
            filters={"gp_task": doc.name},
            fields=["name"],
            limit=1,
        )
        status_map = {
            "Open": "pending",
            "Working": "in_progress",
            "Completed": "completed",
            "Cancelled": "cancelled",
        }
        agent_status = status_map.get(doc.status, "pending")

        if existing:
            # Update existing FF Agent Task
            frappe.db.set_value(
                "FF Agent Task",
                existing[0].name,
                {
                    "title": doc.title or doc.name,
                    "status": agent_status,
                    "description": doc.description or "",
                },
            )
        else:
            # Create new FF Agent Task
            agent_task = frappe.new_doc("FF Agent Task")
            agent_task.title = doc.title or doc.name
            agent_task.status = agent_status
            agent_task.gp_task = doc.name
            agent_task.gp_project = doc.project or ""
            agent_task.description = doc.description or ""
            agent_task.insert(ignore_permissions=True)
        frappe.db.commit()
    finally:
        frappe.flags.in_sync_agent_task = False


def _sync_agent_task_to_gp(doc, method):
    """doc_events hook: when FF Agent Task is created/updated, sync to GP Task."""
    if frappe.flags.in_sync_gp_task:
        return
    frappe.flags.in_sync_gp_task = True
    try:
        if not doc.gp_task:
            # No GP Task linked yet - create one
            gp_task = frappe.new_doc("GP Task")
            gp_task.title = doc.title or doc.name
            gp_task.description = doc.description or ""
            status_map = {
                "pending": "Open",
                "in_progress": "Working",
                "completed": "Completed",
                "cancelled": "Cancelled",
            }
            gp_task.status = status_map.get(doc.status, "Open")
            if doc.gp_project:
                gp_task.project = doc.gp_project
            gp_task.insert(ignore_permissions=True)
            # Link back
            frappe.db.set_value("FF Agent Task", doc.name, "gp_task", gp_task.name)
            frappe.db.commit()
        else:
            # Update existing GP Task
            status_map = {
                "pending": "Open",
                "in_progress": "Working",
                "completed": "Completed",
                "cancelled": "Cancelled",
            }
            gp_status = status_map.get(doc.status, "Open")
            frappe.db.set_value(
                "GP Task",
                doc.gp_task,
                {
                    "title": doc.title or doc.name,
                    "status": gp_status,
                    "description": doc.description or "",
                },
            )
            frappe.db.commit()
    finally:
        frappe.flags.in_sync_gp_task = False
