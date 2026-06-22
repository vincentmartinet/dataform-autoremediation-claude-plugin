import os

GCLOUD = "gcloud"
PID_FILE = "/tmp/dataform-scout.pid"
CONFIG_FILE = os.path.expanduser("~/.config/dataform-scout/config")
LOG_FILTER = 'resource.type="dataform.googleapis.com/Repository" AND severity>=ERROR'
PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(__file__))
)
SKILL_PATH = os.path.join(PLUGIN_ROOT, "skills", "fix-dataform", "SKILL.md")
MAX_FIX_ATTEMPTS = 3
