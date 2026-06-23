"""
Agent Graph Sync — bidirectional bridge between CRM DocTypes and YAML files.

CRM (Frappe DB)  <->  YAML (forsch_frontiers repo)  <->  live-agent-graph (manifest)

Flow:
  1. User edits FF Agent / FF Agent Cluster / FF Agent Task in CRM Desk
  2. Controller on_update hook calls sync.write_*()
  3. YAML files are written to the forsch_frontiers app directory
  4. Git commit + push (optional, configurable)
  5. Cloud box pulls -> live-agent-graph rebuilds manifest -> graph UI updates

Reverse flow (CRM reads YAML):
  1. Whitelisted API endpoint reads YAML files
  2. Returns structured data for the graph server
"""

import logging
import os
from pathlib import Path

import frappe
import yaml

log = logging.getLogger("forsch_frontiers.sync")

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

    # project.md — use yaml.dump for front-matter to avoid injection (#5)
    front_matter = {
        "goal": doc.goal or "",
        "status": doc.status or "blank",
        "handoff_pct": doc.handoff_pct or 0,
        "data_connectors": connectors,
    }
    fm_yaml = yaml.dump(front_matter, default_flow_style=False, sort_keys=False, allow_unicode=True)
    project_md = f"---\n{fm_yaml}---\n# {doc.cluster_id}\n\n{doc.goal or 'New cluster.'}\n"
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
            fields=["agent", "seq"],
            order_by="seq",
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
    # Single query to get all agents with their models (#9 optimization)
    agents = frappe.get_all("FF Agent", fields=["agent_id", "model"])
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
        if a.get("model"):
            all_models.add(a["model"])

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
    """Return the full agent graph manifest for a cluster.

    Reads from DB directly (not from YAML files) to survive redeployments (#4).
    """
    # Verify cluster exists
    if not frappe.db.exists("FF Agent Cluster", {"cluster_id": cluster_id}):
        frappe.throw(f"Cluster '{cluster_id}' not found", frappe.DoesNotExistError)

    # Read cluster config from DB
    cluster_doc = frappe.get_doc("FF Agent Cluster", {"cluster_id": cluster_id})
    member_ids = [m.agent for m in cluster_doc.members]

    # Read agents from DB
    all_agents = frappe.get_all("FF Agent", fields=["agent_id", "title", "description",
                                                     "purpose", "model", "safety_level",
                                                     "role", "group", "status"])
    agents_map = {a["agent_id"]: a for a in all_agents}

    cluster_agents = {}
    for aid in member_ids:
        if aid not in agents_map:
            continue
        a = agents_map[aid]
        tools = frappe.get_all("FF Agent Tool", filters={"parent": aid},
                               fields=["tool_name"], pluck="tool_name")
        channels = frappe.get_all("FF Agent Channel", filters={"parent": aid},
                                  fields=["channel_name"], pluck="channel_name")
        cluster_agents[aid] = {
            "description": a.get("description") or "",
            "discord_channels": channels or [],
            "safety_level": a.get("safety_level") or "read_only",
            "purpose": a.get("purpose") or "",
            "tools": tools or [],
            "model": a.get("model") or "",
            "role": a.get("role") or "plain",
        }

    # Shared components from DB
    all_tools = set()
    all_models = set()
    for a in all_agents:
        tools = frappe.get_all("FF Agent Tool", filters={"parent": a["agent_id"]},
                               fields=["tool_name"], pluck="tool_name")
        all_tools.update(tools)
        if a.get("model"):
            all_models.add(a["model"])

    shared = {
        "tools": sorted(all_tools),
        "models": sorted(all_models),
        "connections": {
            "github": "GitHub (OAuth)",
            "resend": "Resend (email)",
            "cloudflare-global": "Cloudflare (global)",
            "frappe-crm": "Frappe CRM (ff-ops-prod)",
        },
    }

    cluster_config = {
        "name": cluster_doc.cluster_id,
        "description": cluster_doc.goal or "",
        "members": member_ids,
        "config": {"default_model": cluster_doc.default_model or "gpt-5.5"},
    }

    return {
        "cluster": cluster_id,
        "agents": cluster_agents,
        "shared": shared,
        "cluster_config": cluster_config,
    }


@frappe.whitelist(methods=["GET"])
def list_clusters():
    """Return all clusters from the DB (not from YAML files) (#4)."""
    clusters = frappe.get_all(
        "FF Agent Cluster",
        fields=["cluster_id", "goal", "status", "handoff_pct"],
    )
    return [
        {
            "name": c["cluster_id"],
            "goal": c.get("goal") or "",
            "status": c.get("status") or "",
            "handoff_pct": c.get("handoff_pct") or 0,
        }
        for c in clusters
    ]


@frappe.whitelist(methods=["POST"])
def sync_all():
    """Trigger a full sync: CRM -> YAML. Called after bulk changes or on demand."""
    results = write_all()
    return {"ok": True, "files": [{"type": t, "path": p} for t, p in results]}


@frappe.whitelist(methods=["POST"])
def update_agent(agent_id: str, **kwargs):
    """Update an FF Agent record. Accepts field=value pairs for: model, title, role, status, safety_level."""
    import frappe
    if not agent_id:
        frappe.throw("agent_id is required")
    docname = frappe.db.get_value("FF Agent", {"agent_id": agent_id}, "name")
    if not docname:
        frappe.throw(f"Agent '{agent_id}' not found")
    allowed_fields = {"model", "title", "role", "status", "safety_level"}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
    if not updates:
        return {"ok": False, "error": "no valid fields to update"}
    for field, value in updates.items():
        frappe.db.set_value("FF Agent", docname, field, value)
    frappe.db.commit()
    return {"ok": True, "agent_id": agent_id, "updated": list(updates.keys())}


# ── Bidirectional GP Task <-> FF Agent Task sync ──
#
# Uses a SINGLE shared flag to prevent re-entry from either direction (#1).
# No frappe.db.commit() inside hooks — Frappe handles the commit (#2).
# Wrapped in try/except to prevent cross-app exceptions from breaking Gameplan (#3).
# Only syncs GP Tasks that have a project set (scoped, not every GP Task ever) (#3).

_STATUS_MAP_GP_TO_AGENT = {
    "Backlog": "Draft",
    "Todo": "Queued",
    "In Progress": "In Progress",
    "Done": "Complete",
    "Canceled": "Failed",
}

_STATUS_MAP_AGENT_TO_GP = {v: k for k, v in _STATUS_MAP_GP_TO_AGENT.items()}


def _sync_gp_to_agent_task(doc, method):
    """doc_events hook: when GP Task is created/updated, sync to FF Agent Task.

    Only syncs GP Tasks that are associated with an FF Agent Cluster project (#3).
    """
    if frappe.flags.in_gp_agent_sync:
        return
    frappe.flags.in_gp_agent_sync = True
    try:
        # Scope: only sync GP Tasks that have a project set (#3)
        # GP Tasks without a project are internal Gameplan work, not agent tasks.
        if not doc.project:
            return

        existing = frappe.get_all(
            "FF Agent Task",
            filters={"gp_task": doc.name},
            fields=["name"],
            limit=1,
        )
        agent_status = _STATUS_MAP_GP_TO_AGENT.get(doc.status, "Draft")

        if existing:
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
            agent_task = frappe.new_doc("FF Agent Task")
            agent_task.title = doc.title or doc.name
            agent_task.status = agent_status
            agent_task.gp_task = doc.name
            agent_task.gp_project = doc.project or ""
            agent_task.description = doc.description or ""
            agent_task.insert(ignore_permissions=True)
    except Exception:
        log.error("Failed to sync GP Task %s to FF Agent Task", doc.name, exc_info=True)
        frappe.log_error("forsch_frontiers.sync._sync_gp_to_agent_task")
    finally:
        frappe.flags.in_gp_agent_sync = False


def _sync_agent_task_to_gp(doc, method):
    """doc_events hook: when FF Agent Task is created/updated, sync to GP Task."""
    if frappe.flags.in_gp_agent_sync:
        return
    frappe.flags.in_gp_agent_sync = True
    try:
        gp_status = _STATUS_MAP_AGENT_TO_GP.get(doc.status, "Todo")

        # Read the link from the DB, not the in-memory doc: the link-back below
        # uses db.set_value, which does not refresh doc.gp_task. Trusting the
        # attribute would let a re-fire in the same request create a duplicate
        # GP Task. Reading from the DB keeps this hook idempotent.
        gp_task_name = frappe.db.get_value("FF Agent Task", doc.name, "gp_task")

        if not gp_task_name:
            # No GP Task linked yet — create one
            gp_task = frappe.new_doc("GP Task")
            gp_task.title = doc.title or doc.name
            gp_task.description = doc.description or ""
            gp_task.status = gp_status
            if doc.gp_project:
                gp_task.project = doc.gp_project
            gp_task.insert(ignore_permissions=True)
            # Link back. db_set updates the DB *and* the in-memory doc, so any
            # re-fire takes the idempotent "update" branch above.
            doc.db_set("gp_task", gp_task.name)
        else:
            # Update existing GP Task
            frappe.db.set_value(
                "GP Task",
                gp_task_name,
                {
                    "title": doc.title or doc.name,
                    "status": gp_status,
                    "description": doc.description or "",
                },
            )
    except Exception:
        log.error("Failed to sync FF Agent Task %s to GP Task", doc.name, exc_info=True)
        frappe.log_error("forsch_frontiers.sync._sync_agent_task_to_gp")
    finally:
        frappe.flags.in_gp_agent_sync = False
import frappe

@frappe.whitelist(methods=["POST"])
def run_migrate():
    """Run bench migrate to recreate missing tables."""
    import subprocess, os
    result = subprocess.run(
        ["bench", "--site", "crm.forschfrontiers.com", "migrate"],
        capture_output=True, text=True, timeout=120,
        cwd="/app"
    )
    return {"ok": result.returncode == 0, "stdout": result.stdout[-500:], "stderr": result.stderr[-500:]}
