"""Seed FF App Registry with the 21 apps from the original AppMap.

Run on the Railway Frappe instance:
  bench --site crm.forschfrontiers.com execute forsch_frontiers.forsch_frontiers.page.apps_page.seed
"""

import os

import frappe

APPS = [
    # Hubert & companion
    {"app_name": "Hubert chat", "slug": "hubert-chat", "group": "Hubert & companion",
     "url": "https://chat.forschfrontiers.com", "icon": "message-circle"},
    {"app_name": "Huberto", "slug": "huberto", "group": "Hubert & companion",
     "url": "https://huberto.forschfrontiers.com", "icon": "user"},
    {"app_name": "Dashboard", "slug": "dashboard", "group": "Hubert & companion",
     "url": "https://dash.forschfrontiers.com", "icon": "layout"},
    {"app_name": "Companion API", "slug": "companion-api", "group": "Hubert & companion",
     "url": "https://companion-api.forschfrontiers.com", "icon": "share-2"},
    {"app_name": "Vapi voice", "slug": "vapi-voice", "group": "Hubert & companion",
     "url": "https://vapi.forschfrontiers.com", "icon": "phone"},
    {"app_name": "Scarf", "slug": "scarf", "group": "Hubert & companion",
     "url": "https://scarf.forschfrontiers.com", "icon": "cloud"},

    # Work · CRM
    {"app_name": "Frappe CRM", "slug": "frappe-crm", "group": "Work · CRM",
     "url": "https://crm.forschfrontiers.com", "icon": "users"},
    {"app_name": "Team Rooms", "slug": "team-rooms", "group": "Work · CRM",
     "url": "https://crm.forschfrontiers.com/g", "icon": "message-square"},

    # ADK / dev stack · Tailscale
    {"app_name": "Builder cockpit", "slug": "builder-cockpit", "group": "ADK / dev stack",
     "url": os.environ.get("COCKPIT_URL", "https://cockpit.forschfrontiers.com"), "icon": "tool"},
    {"app_name": "LiteLLM proxy", "slug": "litellm-proxy", "group": "ADK / dev stack · Tailscale",
     "url": "http://100.120.21.13:4000", "icon": "cpu",
     "health_url": "http://100.120.21.13:4000/health/readiness"},
    {"app_name": "Rowboat UI", "slug": "rowboat-ui", "group": "ADK / dev stack · Tailscale",
     "url": "https://rowboat.forschfrontiers.com", "icon": "anchor"},
    {"app_name": "rowboatx server", "slug": "rowboatx-server", "group": "ADK / dev stack · Tailscale",
     "url": "http://100.120.21.13:3005", "icon": "git-branch"},
    {"app_name": "Bridge chat", "slug": "bridge-chat", "group": "ADK / dev stack · Tailscale",
     "url": "http://100.120.21.13:8800/chat", "icon": "message-circle",
     "docker_container": "adk-bridge"},
    {"app_name": "Flip-chat", "slug": "flip-chat", "group": "ADK / dev stack · Tailscale",
     "url": "http://100.120.21.13:8801", "icon": "message-square"},

    # Shelby & utilities
    {"app_name": "Paperclip", "slug": "paperclip", "group": "Shelby & utilities",
     "url": "https://paperclip.forschfrontiers.com", "icon": "paperclip"},
    {"app_name": "Groceries", "slug": "groceries", "group": "Shelby & utilities",
     "url": "https://groceries.forschfrontiers.com", "icon": "shopping-cart"},
    {"app_name": "Grocery bridge", "slug": "grocery-bridge", "group": "Shelby & utilities",
     "url": "https://grocery-bridge.forschfrontiers.com", "icon": "link"},
    {"app_name": "Shelby logs", "slug": "shelby-logs", "group": "Shelby & utilities",
     "url": "https://logs-shelby.forschfrontiers.com", "icon": "file-text"},
    {"app_name": "Littlebird MCP", "slug": "littlebird-mcp", "group": "Shelby & utilities",
     "url": "https://littlebird-mcp.forschfrontiers.com", "icon": "feather"},
    {"app_name": "Screening room", "slug": "screening-room", "group": "Shelby & utilities",
     "url": "https://screening-room.forschfrontiers.com", "icon": "film"},

    # Infra
    {"app_name": "Authsome broker", "slug": "authsome-broker", "group": "Infra",
     "url": "https://authsome.forschfrontiers.com", "icon": "key",
     "health_url": "http://100.120.21.13:7998/health"},
]


def execute():
    """Seed the FF App Registry DocType."""
    created = 0
    skipped = 0

    for app in APPS:
        if frappe.db.exists("FF App Registry", app["slug"]):
            skipped += 1
            continue

        doc = frappe.get_doc({
            "doctype": "FF App Registry",
            **app,
            "enabled": 1,
            "status": "unknown",
        })
        doc.insert(ignore_permissions=True)
        created += 1

    frappe.db.commit()
    return {"created": created, "skipped": skipped, "total": len(APPS)}
