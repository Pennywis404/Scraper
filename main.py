#!/usr/bin/env python3
"""
Product Hunt Scraper Bot - Main Entry Point

Usage:
    python main.py          # Run the Telegram bot
    python main.py --test   # Test the workflow without bot
"""

import sys
import asyncio
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def run_bot():
    """Start the Telegram bot."""
    from bot import run_bot as start_bot
    logger.info("Starting Telegram bot...")
    start_bot()


async def test_workflow():
    """Test the workflow without Telegram."""
    from config import get_config
    from database import init_database, LaunchesRepository
    from scraper import ProductHuntClient
    from agents import ClassifierAgent, WorkflowSupervisor, GoogleSheetsExporter

    print("=" * 50)
    print("TEST MODE - Workflow sans Telegram")
    print("=" * 50)

    config = get_config()

    # Init components
    init_database(config.supabase.url, config.supabase.key)

    scraper = ProductHuntClient(
        api_token=config.product_hunt.api_token,
        base_url=config.product_hunt.api_base_url,
        rate_limit_delay=config.product_hunt.rate_limit_delay,
    )

    repository = LaunchesRepository()
    classifier = ClassifierAgent(api_key=config.groq.api_key)

    sheets_exporter = GoogleSheetsExporter(
        credentials=config.google_sheets.credentials,
        spreadsheet_id=config.google_sheets.spreadsheet_id,
    )

    def on_status(msg: str):
        print(f"[STATUS] {msg}")

    supervisor = WorkflowSupervisor(
        scraper=scraper,
        repository=repository,
        classifier=classifier,
        sheets_exporter=sheets_exporter,
        on_status=on_status,
    )

    # Run with small limit for testing
    stats = await supervisor.run(
        limit=5,
        spreadsheet_id=config.google_sheets.spreadsheet_id,
    )

    print("\n" + "=" * 50)
    print("RÉSULTAT:")
    print("=" * 50)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    await scraper.close()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(test_workflow())
    else:
        run_bot()


if __name__ == "__main__":
    main()
