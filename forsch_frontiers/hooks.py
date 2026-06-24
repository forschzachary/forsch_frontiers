app_name = "forsch_frontiers"
app_title = "Forsch Frontiers"
app_publisher = "Zachary Forsch"
app_description = "Forsch Frontiers custom Frappe CRM app"
app_email = "forschzachary@gmail.com"
app_license = "mit"

# Brand theme: Risograph (light) + Modern Sleek (dark), loaded into the Frappe desk.
# Secret third mode: RCT2 Retro, activated via Konami code (↑↑↓↓←→←→BA).
app_include_css = ["/assets/forsch_frontiers/css/forsch-theme.css"]
app_include_js  = ["/assets/forsch_frontiers/js/forsch-easter.js"]

# Fixtures — committed, not hand-edited in Desk.
# Custom Fields with ff_ prefix, CRM Form Scripts, CRM Fields Layouts for CRM Lead.
fixtures = [
    {"dt": "Role", "filters": [["role_name", "=", "FF Ops"]]},
    {"dt": "Custom DocPerm", "filters": [["role", "=", "FF Ops"]]},
    # Panel field (ff_*) + the Twenty integration key. One Custom Field entry only:
    # export overwrites custom_field.json per-doctype, so two entries would collide.
    # Add new app custom fields to this list.
    {"dt": "Custom Field", "filters": [["fieldname", "in", ["ff_related_records_html", "twenty_person_id"]]]},
    {"dt": "CRM Form Script", "filters": [["name", "like", "Forsch%"]]},
    {"dt": "CRM Fields Layout", "filters": [["name", "like", "CRM Lead%"]]},
    # NOTE: Listmonk/Postiz are embedded as in-app CRM views (crm fork routes
    # /newsletters, /social) — the old /listmonk + /postiz Web Pages and the Desk
    # "Marketing" Workspace are removed.
]

# Row-level scoping: hide quarantined (needs_review) subscriptions from scoped roles.
permission_query_conditions = {
    "FF Newsletter Subscription": "forsch_frontiers.permissions.subscription_query_conditions",
}

# Scheduler events for sync jobs (implemented in later phases).
# Spike 001 hooks snippet: listmonk every 15min, postiz every 30min, littlebird every 20min.
scheduler_events = {
    "cron": {
        "*/15 * * * *": [
            "forsch_frontiers.sync.listmonk.run",
        ],
        "*/30 * * * *": [
            "forsch_frontiers.sync.postiz.run",
        ],
        "*/20 * * * *": [
            "forsch_frontiers.sync.littlebird.run",
        ],
    }
}

# Bidirectional sync: GP Task <-> FF Agent Task
# on_update fires on BOTH insert and update in Frappe, so it alone covers
# creation + edits. Do NOT also register after_insert: that double-fires the
# hook on insert, and the FF->GP path would then create a duplicate GP Task
# (the link-back's db.set_value doesn't refresh the in-memory doc.gp_task, so
# the second fire still sees it empty and creates another GP Task).
update_website_context = ["forsch_frontiers.permissions.update_website_context"]

doc_events = {
    "GP Task": {
        "on_update": "forsch_frontiers.sync.agent_graph._sync_gp_to_agent_task",
    },
    "FF Agent Task": {
        "on_update": "forsch_frontiers.sync.agent_graph._sync_agent_task_to_gp",
    },
}
