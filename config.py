from pathlib import Path

BOT_TOKEN = "TOKEN"
ADMIN_IDS = [ID,ID,ID]  # List of admin Telegram IDs

BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "database.db"

# User roles
USER_ROLE_REGULAR = "regular"
USER_ROLE_ADMIN = "admin"

# Post statuses
POST_STATUS_PENDING = "pending"
POST_STATUS_APPROVED = "approved"
POST_STATUS_REJECTED = "rejected"

# User statuses
USER_STATUS_ACTIVE = "active"
USER_STATUS_BLOCKED = "blocked"
