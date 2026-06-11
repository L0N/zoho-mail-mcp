"""
Configuration — loads all settings from environment variables.
Copy .env.example to .env and fill in your values before running.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Anchor to this file's directory so the server works regardless of the
# working directory it is launched from (e.g. by an MCP client).
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

# ─── Zoho OAuth Credentials ──────────────────────────────────────────────────
# Get these from https://api-console.zoho.com/
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI", "http://localhost:8080/callback")

# ─── Zoho API Endpoints ───────────────────────────────────────────────────────
# Zoho has regional data centres — change to .eu, .com.au, .jp if needed
ZOHO_ACCOUNTS_URL = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com")
ZOHO_MAIL_API_URL = os.getenv("ZOHO_MAIL_API_URL", "https://mail.zoho.com/api")

# ─── Local Storage ────────────────────────────────────────────────────────────
# Where OAuth tokens are persisted between server restarts
TOKEN_FILE = os.getenv("TOKEN_FILE", str(BASE_DIR / ".zoho_tokens.json"))

# ─── Validation ───────────────────────────────────────────────────────────────
def validate_config() -> None:
    """Call at startup to catch missing credentials early."""
    missing = []
    if not ZOHO_CLIENT_ID:
        missing.append("ZOHO_CLIENT_ID")
    if not ZOHO_CLIENT_SECRET:
        missing.append("ZOHO_CLIENT_SECRET")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your Zoho API credentials."
        )
