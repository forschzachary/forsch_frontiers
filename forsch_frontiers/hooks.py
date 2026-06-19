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
    {"dt": "Custom Field", "filters": [["fieldname", "like", "ff_%"]]},
    {"dt": "CRM Form Script", "filters": [["name", "like", "Forsch%"]]},
    {"dt": "CRM Fields Layout", "filters": [["name", "like", "CRM Lead%"]]},
]

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
