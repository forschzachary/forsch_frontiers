__version__ = "0.0.1"

# Import API modules at app init so @frappe.whitelist() decorators register.
# Frappe discovers whitelisted methods by importing the module path;
# if the module is never imported, the decorator never fires.
from forsch_frontiers.api import cockpit  # noqa: F401
from forsch_frontiers.api import app_ops  # noqa: F401
from forsch_frontiers.api import ingest   # noqa: F401
from forsch_frontiers.api import parity   # noqa: F401
from forsch_frontiers.api import agent_config   # noqa: F401
from forsch_frontiers.api import agent_factory  # noqa: F401
