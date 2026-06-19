app_name = "forsch_frontiers"
app_title = "Forsch Frontiers"
app_publisher = "Zachary Forsch"
app_description = "Forsch Frontiers custom Frappe CRM app"
app_email = "forschzachary@gmail.com"
app_license = "mit"

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
    # Embedded-tool surfaces (Listmonk now; Postiz later).
    {"dt": "Custom HTML Block", "filters": [["name", "in", ["listmonk-embed"]]]},
    {"dt": "Workspace", "filters": [["name", "=", "Marketing"]]},
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
