# -*- coding: utf-8 -*-
"""Telegram bot command handlers with rich UI."""

from telegram import Update
from telegram.ext import ContextTypes

from config import get_config
from database import init_database, LaunchesRepository
from scraper import ProductHuntClient, IndieHackersClient
from agents import WorkflowSupervisor, ClassifierAgent, GoogleSheetsExporter
from bot.formaters import (
    format_stats, format_status, format_help, format_indie_stats,
    format_main_menu, format_stats_dashboard, format_product_list,
    format_top_products, format_loading, format_error
)
from bot.keyboards import (
    get_main_menu_keyboard, get_view_keyboard, get_stats_keyboard,
    get_scrape_keyboard, get_top_keyboard
)


# Store for pagination state (in production, use Redis or similar)
_view_cache = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        format_main_menu(),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(format_help(), parse_mode="Markdown")


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command - show main menu."""
    await update.message.reply_text(
        format_main_menu(),
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command with rich dashboard."""
    try:
        config = get_config()
        init_database(config.supabase.url, config.supabase.key)
        repo = LaunchesRepository()

        stats = await repo.get_stats()

        await update.message.reply_text(
            format_stats_dashboard(stats),
            parse_mode="Markdown",
            reply_markup=get_stats_keyboard()
        )

    except Exception as e:
        await update.message.reply_text(
            format_error(str(e)),
            parse_mode="Markdown"
        )


async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /view command - browse products with pagination."""
    # Parse filter from args
    filter_type = "all"
    if context.args:
        arg = context.args[0].lower()
        if arg in ["b2b", "b2c"]:
            filter_type = arg

    try:
        config = get_config()
        init_database(config.supabase.url, config.supabase.key)
        repo = LaunchesRepository()

        # Get products based on filter
        if filter_type == "b2b":
            products = await repo.get_by_type("B2B")
        elif filter_type == "b2c":
            products = await repo.get_by_type("B2C")
        else:
            products = await repo.get_all()

        if not products:
            await update.message.reply_text(
                format_error("No products found in database."),
                parse_mode="Markdown"
            )
            return

        # Convert to dicts if needed
        products_list = [p if isinstance(p, dict) else p for p in products]

        # Cache for pagination
        cache_key = f"{update.effective_user.id}:ph"
        _view_cache[cache_key] = products_list

        # Calculate pages
        per_page = 5
        total_pages = (len(products_list) + per_page - 1) // per_page

        await update.message.reply_text(
            format_product_list(products_list, 0, per_page, filter_type, "ph"),
            parse_mode="Markdown",
            reply_markup=get_view_keyboard(0, total_pages, filter_type, "ph")
        )

    except Exception as e:
        await update.message.reply_text(
            format_error(str(e)),
            parse_mode="Markdown"
        )


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /top command - show top revenue products."""
    source = "ph"
    if context.args and context.args[0].lower() == "indie":
        source = "indie"

    try:
        if source == "indie":
            # For indie, we need to scrape fresh data
            await update.message.reply_text(
                format_loading("Fetching Indie Hackers top products"),
                parse_mode="Markdown"
            )

            scraper = IndieHackersClient(headless=True)
            try:
                products = await scraper.get_products(limit=10)
                products_list = [p.to_dict() for p in products]
            finally:
                await scraper.close()
        else:
            # For Product Hunt, get from database
            config = get_config()
            init_database(config.supabase.url, config.supabase.key)
            repo = LaunchesRepository()

            products = await repo.get_all()
            products_list = [p for p in products if p.get("business_type") == "B2B"]

            # Sort by some metric (name for now, could add revenue later)
            products_list = products_list[:10]

        await update.message.reply_text(
            format_top_products(products_list, 10, source),
            parse_mode="Markdown",
            reply_markup=get_top_keyboard(source)
        )

    except Exception as e:
        await update.message.reply_text(
            format_error(str(e)),
            parse_mode="Markdown"
        )


async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scrape command with enhanced UI."""
    limit = 50
    if context.args and context.args[0].isdigit():
        limit = int(context.args[0])

    chat_id = update.effective_chat.id

    # Send loading message
    loading_msg = await update.message.reply_text(
        format_loading("Scraping Product Hunt"),
        parse_mode="Markdown"
    )

    async def send_status(message: str):
        """Update status in the loading message."""
        formatted = format_status(message)
        try:
            await context.bot.send_message(chat_id=chat_id, text=formatted)
        except:
            pass

    try:
        config = get_config()
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

        supervisor = WorkflowSupervisor(
            scraper=scraper,
            repository=repository,
            classifier=classifier,
            sheets_exporter=sheets_exporter,
            on_status=send_status,
        )

        stats = await supervisor.run(
            limit=limit,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
        )

        # Delete loading message
        await loading_msg.delete()

        # Send final result with keyboard
        await update.message.reply_text(
            format_stats(stats),
            parse_mode="Markdown",
            reply_markup=get_scrape_keyboard("ph")
        )

        await scraper.close()

    except Exception as e:
        await loading_msg.delete()
        await update.message.reply_text(
            format_error(str(e)),
            parse_mode="Markdown"
        )


async def indie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /indie command with enhanced UI."""
    limit = 50
    if context.args and context.args[0].isdigit():
        limit = int(context.args[0])

    chat_id = update.effective_chat.id

    # Send loading message
    loading_msg = await update.message.reply_text(
        format_loading("Scraping Indie Hackers"),
        parse_mode="Markdown"
    )

    async def send_status(message: str):
        formatted = format_status(message)
        try:
            await context.bot.send_message(chat_id=chat_id, text=formatted)
        except:
            pass

    try:
        config = get_config()

        await send_status(f"🔍 Fetching {limit} products...")

        scraper = IndieHackersClient(headless=True)

        try:
            products = await scraper.get_products(limit=limit)
            await send_status(f"✅ {len(products)} products found")

            await send_status("📊 Exporting to Google Sheets...")

            sheets_exporter = GoogleSheetsExporter(
                credentials=config.google_sheets.credentials,
                spreadsheet_id=config.google_sheets.spreadsheet_id,
            )

            exported = sheets_exporter.export_indie_products(
                products,
                spreadsheet_id=config.google_sheets.spreadsheet_id,
            )

            # Cache products for viewing
            cache_key = f"{update.effective_user.id}:indie"
            _view_cache[cache_key] = [p.to_dict() for p in products]

            stats = {
                "scraped": len(products),
                "exported": exported,
            }

            # Delete loading message
            await loading_msg.delete()

            await update.message.reply_text(
                format_indie_stats(stats),
                parse_mode="Markdown",
                reply_markup=get_scrape_keyboard("indie")
            )

        finally:
            await scraper.close()

    except Exception as e:
        await loading_msg.delete()
        await update.message.reply_text(
            format_error(str(e)),
            parse_mode="Markdown"
        )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split(":")

    if parts[0] == "noop":
        return

    elif parts[0] == "menu":
        if parts[1] == "main":
            await query.edit_message_text(
                format_main_menu(),
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )

        elif parts[1] == "stats":
            try:
                config = get_config()
                init_database(config.supabase.url, config.supabase.key)
                repo = LaunchesRepository()
                stats = await repo.get_stats()

                await query.edit_message_text(
                    format_stats_dashboard(stats),
                    parse_mode="Markdown",
                    reply_markup=get_stats_keyboard()
                )
            except Exception as e:
                await query.edit_message_text(
                    format_error(str(e)),
                    parse_mode="Markdown"
                )

    elif parts[0] == "view":
        filter_type = parts[1]
        page = int(parts[2])
        source = parts[3] if len(parts) > 3 else "ph"
        refresh = len(parts) > 4 and parts[4] == "refresh"

        try:
            cache_key = f"{query.from_user.id}:{source}"

            # Get products from cache or fetch fresh
            if refresh or cache_key not in _view_cache:
                if source == "indie":
                    scraper = IndieHackersClient(headless=True)
                    try:
                        products = await scraper.get_products(limit=50)
                        products_list = [p.to_dict() for p in products]
                    finally:
                        await scraper.close()
                else:
                    config = get_config()
                    init_database(config.supabase.url, config.supabase.key)
                    repo = LaunchesRepository()
                    products_list = await repo.get_all()

                _view_cache[cache_key] = products_list
            else:
                products_list = _view_cache[cache_key]

            # Apply filter
            if filter_type == "b2b":
                filtered = [p for p in products_list if p.get("business_type") == "B2B"]
            elif filter_type == "b2c":
                filtered = [p for p in products_list if p.get("business_type") == "B2C"]
            else:
                filtered = products_list

            if not filtered:
                await query.edit_message_text(
                    format_error("No products found with this filter."),
                    parse_mode="Markdown",
                    reply_markup=get_view_keyboard(0, 1, filter_type, source)
                )
                return

            per_page = 5
            total_pages = (len(filtered) + per_page - 1) // per_page
            page = min(page, total_pages - 1)

            await query.edit_message_text(
                format_product_list(filtered, page, per_page, filter_type, source),
                parse_mode="Markdown",
                reply_markup=get_view_keyboard(page, total_pages, filter_type, source)
            )

        except Exception as e:
            await query.edit_message_text(
                format_error(str(e)),
                parse_mode="Markdown"
            )

    elif parts[0] == "top":
        source = parts[1]

        try:
            if source == "indie":
                await query.edit_message_text(
                    format_loading("Fetching Indie Hackers top products"),
                    parse_mode="Markdown"
                )

                scraper = IndieHackersClient(headless=True)
                try:
                    products = await scraper.get_products(limit=10)
                    products_list = [p.to_dict() for p in products]
                finally:
                    await scraper.close()
            else:
                config = get_config()
                init_database(config.supabase.url, config.supabase.key)
                repo = LaunchesRepository()

                products = await repo.get_all()
                products_list = [p for p in products if p.get("business_type") == "B2B"][:10]

            await query.edit_message_text(
                format_top_products(products_list, 10, source),
                parse_mode="Markdown",
                reply_markup=get_top_keyboard(source)
            )

        except Exception as e:
            await query.edit_message_text(
                format_error(str(e)),
                parse_mode="Markdown"
            )

    elif parts[0] == "cancel":
        await query.edit_message_text(
            "❌ Action cancelled.",
            parse_mode="Markdown"
        )
