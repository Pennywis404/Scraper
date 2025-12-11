# -*- coding: utf-8 -*-
"""Message formatters for Telegram bot with rich UI."""

import re
from typing import Optional


def _progress_bar(value: int, total: int, length: int = 10) -> str:
    """Create a visual progress bar."""
    if total == 0:
        return "░" * length
    filled = int((value / total) * length)
    return "█" * filled + "░" * (length - filled)


def _truncate(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


def _escape_markdown(text: str) -> str:
    """Escape Markdown special characters to prevent parsing errors."""
    if not text:
        return ""
    # Escape these characters: * _ ` [ ]
    for char in ['*', '_', '`', '[', ']']:
        text = text.replace(char, '\\' + char)
    return text


def _format_revenue(revenue: str) -> str:
    """Format revenue with emoji based on amount."""
    if not revenue:
        return "—"

    # Extract numeric value
    match = re.search(r'\$?([\d,]+)', revenue)
    if match:
        amount = int(match.group(1).replace(",", ""))
        if amount >= 100000:
            return f"💰 {revenue}"
        elif amount >= 10000:
            return f"💵 {revenue}"
        else:
            return f"💲 {revenue}"
    return revenue


def format_stats(stats: dict) -> str:
    """Format workflow stats for Telegram message."""
    lines = [
        "📊 *WORKFLOW COMPLETE*",
        "",
    ]

    # Scraping stats
    lines.append(f"🔍 *Scraping*")
    lines.append(f"   Products found: `{stats.get('scraped', 0)}`")
    lines.append(f"   Stored in DB: `{stats.get('stored', 0)}`")

    # Classification stats
    if stats.get("classified", 0) > 0:
        b2b = stats.get('b2b_count', 0)
        b2c = stats.get('b2c_count', 0)
        total = b2b + b2c

        lines.append("")
        lines.append(f"🏷️ *Classification*")
        lines.append(f"   🏢 B2B: `{b2b}` {_progress_bar(b2b, total)}")
        lines.append(f"   🛍️ B2C: `{b2c}` {_progress_bar(b2c, total)}")

    # Export stats
    if stats.get("exported", 0) > 0:
        lines.append("")
        lines.append(f"📤 *Export Google Sheets*")
        lines.append(f"   B2B Products: `{stats.get('b2b_exported', 0)}`")
        lines.append(f"   Startup Tracker: `{stats.get('other_exported', 0)}`")

    # Errors
    if stats.get("errors"):
        lines.append("")
        lines.append("⚠️ *Errors:*")
        for error in stats["errors"]:
            lines.append(f"   {error}")

    return "\n".join(lines)


def format_status(message: str) -> str:
    """Format a status message with emoji."""
    if "..." in message or "en cours" in message.lower():
        return f"⏳ {message}"
    return message


def format_indie_stats(stats: dict) -> str:
    """Format Indie Hackers workflow stats."""
    lines = [
        "🚀 *INDIE HACKERS SCRAPE*",
        "",
        f"🔍 Products scraped: `{stats.get('scraped', 0)}`",
        f"📤 Exported to sheet: `{stats.get('exported', 0)}`",
        "",
        "📋 Sheet: `Indie Hackers`",
    ]
    return "\n".join(lines)


def format_help() -> str:
    """Format help message with nice UI."""
    return """🤖 *STARTUP SCRAPER*

*Scraping*
• `/scrape` — Product Hunt workflow
• `/scrape 20` — Limit to 20 products
• `/indie` — Indie Hackers scrape
• `/indie 20` — Limit to 20 products

*Dashboard*
• `/menu` — Main menu with buttons
• `/stats` — Database statistics
• `/view` — Browse all products
• `/top` — Top revenue products
• `/help` — This help message

*Workflows*

Product Hunt:
  1. Scrape API
  2. Store in Supabase
  3. Classify B2B/B2C
  4. Export to Sheets

Indie Hackers:
  1. Scrape website
  2. Export to Sheets
"""


def format_main_menu() -> str:
    """Format main menu message."""
    return """🏠 *MAIN MENU*

Choose an action below:"""


def format_stats_dashboard(stats: dict) -> str:
    """Format detailed stats dashboard."""
    total = stats.get('total', 0)
    b2b = stats.get('b2b', 0)
    b2c = stats.get('b2c', 0)
    unknown = stats.get('unknown', 0)

    # Calculate percentages
    b2b_pct = (b2b / total * 100) if total > 0 else 0
    b2c_pct = (b2c / total * 100) if total > 0 else 0

    lines = [
        "📊 *DATABASE STATS*",
        "",
        f"📦 *Total Products:* `{total}`",
        "",
        "*By Type*",
        "",
        f"🏢 B2B: `{b2b}` ({b2b_pct:.0f}%)",
        f"   {_progress_bar(b2b, total, 15)}",
        "",
        f"🛍️ B2C: `{b2c}` ({b2c_pct:.0f}%)",
        f"   {_progress_bar(b2c, total, 15)}",
        "",
        f"❓ Unknown: `{unknown}`",
    ]

    return "\n".join(lines)


def format_product_card(
    product: dict,
    index: int = 0,
    show_rank: bool = False
) -> str:
    """Format a single product as a card."""
    name = _escape_markdown(product.get("name", "Unknown"))
    tagline = _escape_markdown(_truncate(product.get("tagline", ""), 60))
    website = _escape_markdown(product.get("website", ""))
    business_type = product.get("business_type", "")
    revenue = _escape_markdown(product.get("revenue", ""))

    # Type emoji
    if business_type == "B2B":
        type_emoji = "🏢"
    elif business_type == "B2C":
        type_emoji = "🛍️"
    else:
        type_emoji = "❓"

    # Rank prefix
    rank = ""
    if show_rank:
        medals = ["🥇", "🥈", "🥉"]
        rank = medals[index] if index < 3 else f"#{index + 1}"
        rank = f"{rank} "

    lines = [f"{rank}*{name}* {type_emoji}"]

    if tagline:
        lines.append(f"_{tagline}_")

    if revenue:
        lines.append(f"{_format_revenue(revenue)}")

    if website:
        lines.append(f"🔗 {website}")

    return "\n".join(lines)


def format_indie_product_card(
    product: dict,
    index: int = 0,
    show_rank: bool = False
) -> str:
    """Format an Indie Hackers product card."""
    name = _escape_markdown(product.get("name", "Unknown"))
    tagline = _escape_markdown(_truncate(product.get("tagline", ""), 60))
    revenue = _escape_markdown(product.get("revenue", ""))
    stripe = product.get("stripe_verified", False)
    url = product.get("url", "")  # URL not escaped for links

    # Stripe badge
    stripe_badge = "✅" if stripe else "❌"

    # Rank prefix
    rank = ""
    if show_rank:
        medals = ["🥇", "🥈", "🥉"]
        rank = medals[index] if index < 3 else f"#{index + 1}"
        rank = f"{rank} "

    lines = [f"{rank}*{name}*"]

    if tagline:
        lines.append(f"_{tagline}_")

    if revenue:
        lines.append(f"{_format_revenue(revenue)} {stripe_badge}")

    if url:
        lines.append(f"🔗 [View]({url})")

    return "\n".join(lines)


def format_product_list(
    products: list,
    page: int = 0,
    per_page: int = 5,
    filter_type: str = "all",
    source: str = "ph"
) -> str:
    """Format a paginated list of products."""
    total = len(products)
    start = page * per_page
    end = min(start + per_page, total)
    page_products = products[start:end]

    # Filter label
    filter_labels = {
        "all": "📋 All Products",
        "b2b": "🏢 B2B Products",
        "b2c": "🛍️ B2C Products",
    }
    filter_label = filter_labels.get(filter_type, "📋 Products")

    # Source label
    source_label = "Product Hunt" if source == "ph" else "Indie Hackers"

    lines = [
        f"{filter_label}",
        "",
        f"📍 Source: {source_label}",
        f"📊 Showing {start + 1}-{end} of {total}",
        "",
    ]

    # Format each product
    for i, product in enumerate(page_products):
        if source == "indie":
            lines.append(format_indie_product_card(product, start + i))
        else:
            lines.append(format_product_card(product, start + i))
        lines.append("")

    return "\n".join(lines)


def format_top_products(
    products: list,
    limit: int = 10,
    source: str = "ph"
) -> str:
    """Format top products by revenue."""
    source_label = "Product Hunt" if source == "ph" else "Indie Hackers"
    source_emoji = "🏆" if source == "ph" else "🚀"

    lines = [
        f"{source_emoji} *TOP {limit} REVENUE*",
        "",
        f"📍 Source: {source_label}",
        "",
    ]

    for i, product in enumerate(products[:limit]):
        if source == "indie":
            lines.append(format_indie_product_card(product, i, show_rank=True))
        else:
            lines.append(format_product_card(product, i, show_rank=True))
        lines.append("")

    return "\n".join(lines)


def format_loading(action: str = "Loading") -> str:
    """Format a loading message."""
    return f"⏳ *{action}...*\n\nPlease wait..."


def format_error(error: str) -> str:
    """Format an error message."""
    return f"❌ *ERROR*\n\n{error}\n\nTry again or use /help for assistance."


def format_success(message: str) -> str:
    """Format a success message."""
    return f"✅ *SUCCESS*\n\n{message}"
