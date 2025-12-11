"""Telegram bot entry point with enhanced UI."""

import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import get_config
from bot.handlers import (
    start_command,
    help_command,
    menu_command,
    stats_command,
    view_command,
    top_command,
    scrape_command,
    indie_command,
    callback_handler,
)


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def create_bot() -> Application:
    """Create and configure the Telegram bot."""
    config = get_config()

    # Create application
    application = Application.builder().token(config.telegram.bot_token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("view", view_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("scrape", scrape_command))
    application.add_handler(CommandHandler("indie", indie_command))

    # Register callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(callback_handler))

    return application


def run_bot():
    """Run the bot."""
    logger.info("Starting Startup Scraper Bot with Dashboard UI...")

    application = create_bot()
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    run_bot()
