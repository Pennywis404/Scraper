import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Project root directory
ROOT_DIR = Path(__file__).parent

# Load environment variables from explicit path
load_dotenv(ROOT_DIR / ".env", override=True)


def _get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first (for Streamlit Cloud)
    # Only attempt if streamlit is already loaded (avoid import conflicts with telegram bot)
    import sys
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    # Fallback to environment variable
    return os.getenv(key, default)


@dataclass
class TelegramConfig:
    bot_token: str


@dataclass
class GroqConfig:
    api_key: str


@dataclass
class GeminiConfig:
    api_key: str


@dataclass
class SupabaseConfig:
    url: str
    key: str


@dataclass
class ProductHuntConfig:
    api_token: str
    api_base_url: str
    rate_limit_delay: int
    output_dir: str


@dataclass
class GoogleSheetsConfig:
    credentials_path: Path
    credentials: dict
    spreadsheet_id: Optional[str] = None


@dataclass
class Config:
    telegram: TelegramConfig
    groq: GroqConfig
    gemini: GeminiConfig
    supabase: SupabaseConfig
    product_hunt: ProductHuntConfig
    google_sheets: GoogleSheetsConfig


def _load_json_credentials(relative_path: str) -> dict:
    """Load JSON credentials from file or Streamlit secrets."""
    # Try Streamlit secrets first (for Streamlit Cloud)
    import sys
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "google_sheets" in st.secrets:
                return dict(st.secrets["google_sheets"])
        except Exception:
            pass

    # Fallback to file
    full_path = ROOT_DIR / relative_path
    if not full_path.exists():
        return {}
    with open(full_path, "r") as f:
        return json.load(f)


def load_config() -> Config:
    """Load and validate all configuration."""

    # Google Sheets credentials path
    gs_creds_path = _get_secret("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials/google_sheets.json")

    return Config(
        telegram=TelegramConfig(
            bot_token=_get_secret("TELEGRAM_BOT_TOKEN", ""),
        ),
        groq=GroqConfig(
            api_key=_get_secret("GROQ_API_KEY", ""),
        ),
        gemini=GeminiConfig(
            api_key=_get_secret("GEMINI_API_CENTRAL_KEY", ""),
        ),
        supabase=SupabaseConfig(
            url=_get_secret("SUPABASE_URL", ""),
            key=_get_secret("SUPABASE_KEY", ""),
        ),
        product_hunt=ProductHuntConfig(
            api_token=_get_secret("PRODUCT_HUNT_API_TOKEN", ""),
            api_base_url=_get_secret("API_BASE_URL", "https://api.producthunt.com/v2/api/graphql"),
            rate_limit_delay=int(_get_secret("RATE_LIMIT_DELAY", "1")),
            output_dir=_get_secret("OUTPUT_DIR", "data"),
        ),
        google_sheets=GoogleSheetsConfig(
            credentials_path=ROOT_DIR / gs_creds_path,
            credentials=_load_json_credentials(gs_creds_path),
            spreadsheet_id=_get_secret("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
        ),
    )


# Lazy loading singleton
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the configuration singleton. Loads on first call."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
