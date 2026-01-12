#!/usr/bin/env python3
"""
Product Hunt Scraper Bot - Main Entry Point

Usage:
    python main.py                          # Run the Telegram bot
    python main.py --scrape                 # Run scraper (default: 50 products from Product Hunt)
    python main.py --scrape --limit 100     # Scrape 100 products
    python main.py --scrape --source ih     # Scrape from Indie Hackers
    python main.py --scrape --source all    # Scrape from both sources
"""

import sys
import asyncio
import argparse
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


async def run_scraper(limit: int = 50, source: str = "ph"):
    """Run the scraper workflow without Telegram.

    Args:
        limit: Number of products to scrape
        source: 'ph' for Product Hunt, 'ih' for Indie Hackers, 'all' for both
    """
    from config import get_config
    from database import init_database, LaunchesRepository
    from scraper import ProductHuntClient
    from agents import ClassifierAgent, WorkflowSupervisor, GoogleSheetsExporter

    print("=" * 50)
    print(f"SCRAPER - Source: {source}, Limit: {limit}")
    print("=" * 50)

    config = get_config()

    # Init components
    init_database(config.supabase.url, config.supabase.key)

    scraper = None
    ih_scraper = None

    if source in ("ph", "all"):
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

    all_stats = {}

    # Scrape Product Hunt
    if source in ("ph", "all") and scraper:
        print("\n📦 Scraping Product Hunt...")
        supervisor = WorkflowSupervisor(
            scraper=scraper,
            repository=repository,
            classifier=classifier,
            sheets_exporter=sheets_exporter,
            on_status=on_status,
        )

        stats = await supervisor.run(
            limit=limit,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
        )
        all_stats["product_hunt"] = stats
        await scraper.close()

    # Scrape Indie Hackers
    if source in ("ih", "all"):
        print("\n🚀 Scraping Indie Hackers...")
        from scraper.indiehackers import IndieHackersScraper

        ih_scraper = IndieHackersScraper()
        await ih_scraper.init()

        supervisor_ih = WorkflowSupervisor(
            scraper=ih_scraper,
            repository=repository,
            classifier=classifier,
            sheets_exporter=sheets_exporter,
            on_status=on_status,
        )

        stats_ih = await supervisor_ih.run(
            limit=limit,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
        )
        all_stats["indie_hackers"] = stats_ih
        await ih_scraper.close()

    print("\n" + "=" * 50)
    print("RÉSULTAT:")
    print("=" * 50)
    for source_name, stats in all_stats.items():
        print(f"\n{source_name}:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(description="Startup Scraper")
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="Run the scraper (without Telegram bot)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Alias for --scrape with limit=5 (backward compatibility)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of products to scrape (default: 50)",
    )
    parser.add_argument(
        "--source",
        choices=["ph", "ih", "all"],
        default="ph",
        help="Source: ph=Product Hunt, ih=Indie Hackers, all=both (default: ph)",
    )

    args = parser.parse_args()

    if args.scrape:
        asyncio.run(run_scraper(limit=args.limit, source=args.source))
    elif args.test:
        # Backward compatibility
        asyncio.run(run_scraper(limit=5, source="ph"))
    else:
        run_bot()


if __name__ == "__main__":
    main()
