"""Add Agent Builder shortcut to the Frappe CRM workspace."""
import frappe
import json


def execute():
    ws = frappe.get_doc("Workspace", "Frappe CRM")

    # Skip if shortcut already exists
    if any(s.label == "Agent Builder" for s in ws.shortcuts):
        return

    # Add Workspace Shortcut child row
    ws.append("shortcuts", {
        "type": "URL",
        "label": "Agent Builder",
        "url": "/agent-builder",
        "icon": "graph",
        "color": "Blue",
        "idx": len(ws.shortcuts) + 1,
    })

    # Add a content block referencing the shortcut
    content = json.loads(ws.content) if ws.content else []
    # Insert at position 1 (after PORTAL header)
    content.insert(1, {
        "id": "ff-agent-builder-sc",
        "type": "shortcut",
        "data": {"shortcut_name": "Agent Builder", "col": 3},
    })
    ws.content = json.dumps(content)

    ws.save(ignore_permissions=True)
    frappe.db.commit()
