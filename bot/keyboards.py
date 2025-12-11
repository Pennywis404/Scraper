# -*- coding: utf-8 -*-
"""Inline keyboards for Telegram bot UI."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu with quick actions."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Stats", callback_data="menu:stats"),
            InlineKeyboardButton("👀 View All", callback_data="view:all:0"),
        ],
        [
            InlineKeyboardButton("🏢 B2B Only", callback_data="view:b2b:0"),
            InlineKeyboardButton("🛍️ B2C Only", callback_data="view:b2c:0"),
        ],
        [
            InlineKeyboardButton("🏆 Top Revenue", callback_data="top:ph"),
            InlineKeyboardButton("🚀 Indie Top", callback_data="top:indie"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_view_keyboard(
    current_page: int,
    total_pages: int,
    filter_type: str = "all",
    source: str = "ph"
) -> InlineKeyboardMarkup:
    """Pagination keyboard for viewing products."""
    keyboard = []

    # Navigation row
    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(
            "◀️ Prev",
            callback_data=f"view:{filter_type}:{current_page - 1}:{source}"
        ))

    nav_row.append(InlineKeyboardButton(
        f"📄 {current_page + 1}/{total_pages}",
        callback_data="noop"
    ))

    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            "Next ▶️",
            callback_data=f"view:{filter_type}:{current_page + 1}:{source}"
        ))

    keyboard.append(nav_row)

    # Filter row
    filter_row = [
        InlineKeyboardButton(
            "✅ All" if filter_type == "all" else "All",
            callback_data=f"view:all:0:{source}"
        ),
        InlineKeyboardButton(
            "✅ B2B" if filter_type == "b2b" else "B2B",
            callback_data=f"view:b2b:0:{source}"
        ),
        InlineKeyboardButton(
            "✅ B2C" if filter_type == "b2c" else "B2C",
            callback_data=f"view:b2c:0:{source}"
        ),
    ]
    keyboard.append(filter_row)

    # Back to menu
    keyboard.append([
        InlineKeyboardButton("🏠 Menu", callback_data="menu:main"),
        InlineKeyboardButton("🔄 Refresh", callback_data=f"view:{filter_type}:{current_page}:{source}:refresh"),
    ])

    return InlineKeyboardMarkup(keyboard)


def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for stats view."""
    keyboard = [
        [
            InlineKeyboardButton("👀 View Products", callback_data="view:all:0"),
            InlineKeyboardButton("🏆 Top Revenue", callback_data="top:ph"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh Stats", callback_data="menu:stats:refresh"),
        ],
        [
            InlineKeyboardButton("🏠 Menu", callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_scrape_keyboard(source: str = "ph") -> InlineKeyboardMarkup:
    """Keyboard shown after scraping."""
    keyboard = [
        [
            InlineKeyboardButton("👀 View Results", callback_data=f"view:all:0:{source}"),
            InlineKeyboardButton("📊 Stats", callback_data="menu:stats"),
        ],
        [
            InlineKeyboardButton(
                "📋 Open Google Sheets",
                url="https://docs.google.com/spreadsheets"  # Will be replaced with actual URL
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_top_keyboard(source: str = "ph") -> InlineKeyboardMarkup:
    """Keyboard for top products view."""
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Product Hunt" if source == "ph" else "Product Hunt",
                callback_data="top:ph"
            ),
            InlineKeyboardButton(
                "✅ Indie Hackers" if source == "indie" else "Indie Hackers",
                callback_data="top:indie"
            ),
        ],
        [
            InlineKeyboardButton("👀 View All", callback_data=f"view:all:0:{source}"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{action}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
