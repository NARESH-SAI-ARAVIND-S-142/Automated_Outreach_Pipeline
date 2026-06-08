"""
Configuration loader — reads API keys and sender info from .env file.
Fails fast with clear error messages if any required key is missing.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os


# Load .env from project root
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)


def _require(key: str) -> str:
    """Get a required environment variable or exit with a helpful message."""
    value = os.getenv(key, "").strip()
    if not value or value.startswith("your_"):
        print(f"\n❌  Missing required env var: {key}")
        print(f"   → Copy .env.example to .env and fill in your keys.")
        print(f"   → Variable '{key}' is required.\n")
        sys.exit(1)
    return value


def _optional(key: str, default: str = "") -> str:
    """Get an optional environment variable with a default."""
    return os.getenv(key, default).strip() or default


# ── API Keys ───────────────────────────────────────────────
# Ocean.io is optional — the pipeline supports --mock-ocean mode
OCEAN_API_TOKEN  = _optional("OCEAN_API_TOKEN")
PROSPEO_API_KEY  = _require("PROSPEO_API_KEY")
BREVO_API_KEY    = _require("BREVO_API_KEY")

# Eazyreach is optional — we fall back to Prospeo if unavailable
EAZYREACH_API_KEY = _optional("EAZYREACH_API_KEY")

# ── Sender Info ────────────────────────────────────────────
SENDER_EMAIL = _require("SENDER_EMAIL")
SENDER_NAME  = _require("SENDER_NAME")

# ── API Endpoints ──────────────────────────────────────────
OCEAN_BASE_URL     = "https://api.ocean.io/v3"
PROSPEO_BASE_URL   = "https://api.prospeo.io"
EAZYREACH_BASE_URL = "https://api.eazyreach.app"   # Placeholder — update when docs available
BREVO_BASE_URL     = "https://api.brevo.com/v3"

# ── Runtime Flags (set by CLI) ─────────────────────────────
MOCK_OCEAN = False  # Set to True via --mock-ocean CLI flag

# ── Defaults ───────────────────────────────────────────────
DEFAULT_MAX_COMPANIES           = 10
DEFAULT_MAX_CONTACTS_PER_COMPANY = 5
REQUEST_TIMEOUT                 = (30, 60)   # (connect, read) in seconds
MAX_RETRIES                     = 3
RETRY_BACKOFF_FACTOR            = 2
