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
    """Load JSON credentials from a file path relative to project root."""
    full_path = ROOT_DIR / relative_path
    if not full_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {full_path}\n"
            f"Please place your Google Sheets service account JSON at: {relative_path}"
        )
    with open(full_path, "r") as f:
        return json.load(f)


def load_config() -> Config:
    """Load and validate all configuration."""

    # Google Sheets credentials path
    gs_creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials/google_sheets.json")

    return Config(
        telegram=TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        ),
        groq=GroqConfig(
            api_key=os.getenv("GROQ_API_KEY", ""),
        ),
        gemini=GeminiConfig(
            api_key=os.getenv("GEMINI_API_CENTRAL_KEY", ""),
        ),
        supabase=SupabaseConfig(
            url=os.getenv("SUPABASE_URL", ""),
            key=os.getenv("SUPABASE_KEY", ""),
        ),
        product_hunt=ProductHuntConfig(
            api_token=os.getenv("PRODUCT_HUNT_API_TOKEN", ""),
            api_base_url=os.getenv("API_BASE_URL", "https://api.producthunt.com/v2/api/graphql"),
            rate_limit_delay=int(os.getenv("RATE_LIMIT_DELAY", "1")),
            output_dir=os.getenv("OUTPUT_DIR", "data"),
        ),
        google_sheets=GoogleSheetsConfig(
            credentials_path=ROOT_DIR / gs_creds_path,
            credentials=_load_json_credentials(gs_creds_path),
            spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
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
