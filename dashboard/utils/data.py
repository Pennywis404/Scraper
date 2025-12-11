# -*- coding: utf-8 -*-
"""
Data loading utilities for the dashboard.
Handles both Product Hunt (Supabase) and Indie Hackers (scraper) data.
"""

import streamlit as st
from enum import Enum
from typing import Optional
from datetime import datetime
import re


class DataSource(Enum):
    PRODUCT_HUNT = "Product Hunt"
    INDIE_HACKERS = "Indie Hackers"
    ALL = "All Sources"


# Column definitions for each source
COLUMN_CONFIG = {
    DataSource.PRODUCT_HUNT: {
        "columns": ["name", "tagline", "business_type", "votes_count", "comments_count", "website", "topics"],
        "display_names": {
            "name": "Name",
            "tagline": "Tagline",
            "business_type": "Type",
            "votes_count": "Votes",
            "comments_count": "Comments",
            "website": "Website",
            "topics": "Topics",
        },
        "sortable": ["votes_count", "comments_count", "name"],
        "filterable": ["business_type"],
    },
    DataSource.INDIE_HACKERS: {
        "columns": ["name", "tagline", "revenue", "stripe_verified", "url"],
        "display_names": {
            "name": "Name",
            "tagline": "Tagline",
            "revenue": "Revenue",
            "stripe_verified": "Verified",
            "url": "Link",
        },
        "sortable": ["revenue", "name"],
        "filterable": ["stripe_verified"],
    },
}


def _get_repo():
    """Get the launches repository."""
    from database.repositories.launches import LaunchesRepository
    return LaunchesRepository()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_quick_stats() -> dict:
    """Get quick stats for sidebar display."""
    try:
        import asyncio
        repo = _get_repo()

        # Run async function synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stats = loop.run_until_complete(repo.get_stats())
        finally:
            loop.close()

        return stats
    except Exception as e:
        st.error(f"Error loading stats: {e}")
        return {"total": 0, "b2b": 0, "b2c": 0, "unknown": 0}


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_recent_products(limit: int = 10) -> list[dict]:
    """Get most recently added products."""
    try:
        import asyncio
        repo = _get_repo()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            products = loop.run_until_complete(repo.get_all())
        finally:
            loop.close()

        # Sort by created_at descending (most recent first)
        sorted_products = sorted(
            products,
            key=lambda x: x.get("created_at") or "",
            reverse=True
        )

        return sorted_products[:limit]
    except Exception as e:
        st.error(f"Error loading recent products: {e}")
        return []


@st.cache_data(ttl=60)
def get_all_products() -> list[dict]:
    """Get all Product Hunt products from Supabase."""
    try:
        import asyncio
        repo = _get_repo()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            products = loop.run_until_complete(repo.get_all())
        finally:
            loop.close()

        # Add source field
        for p in products:
            p["_source"] = "Product Hunt"

        return products
    except Exception as e:
        st.error(f"Error loading products: {e}")
        return []


@st.cache_data(ttl=60)
def get_products_by_type(business_type: str) -> list[dict]:
    """Get products filtered by business type."""
    try:
        import asyncio
        repo = _get_repo()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            products = loop.run_until_complete(repo.get_by_type(business_type))
        finally:
            loop.close()

        return products
    except Exception as e:
        st.error(f"Error loading products: {e}")
        return []


def get_indie_products(limit: int = 50, use_cache: bool = True) -> list[dict]:
    """
    Get Indie Hackers products.
    Uses session cache if available, otherwise scrapes fresh.
    """
    # Check cache first
    if use_cache and st.session_state.get("indie_cache"):
        return st.session_state.indie_cache[:limit]

    return []  # Return empty if no cache - scraping should be done via Settings page


async def scrape_indie_products_async(limit: int = 50) -> list[dict]:
    """Scrape fresh Indie Hackers products (async)."""
    from scraper.indiehackers import IndieHackersClient

    client = IndieHackersClient(headless=True)
    try:
        products = await client.get_products(limit=limit)
        products_list = [p.to_dict() for p in products]

        # Add source field
        for p in products_list:
            p["_source"] = "Indie Hackers"

        # Update cache
        st.session_state.indie_cache = products_list
        st.session_state.last_indie_scrape = datetime.now()

        return products_list
    finally:
        await client.close()


def parse_revenue(revenue_str: str) -> int:
    """Parse revenue string to integer for sorting."""
    if not revenue_str:
        return 0
    match = re.search(r'\$?([\d,]+)', revenue_str)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0


def get_column_config(source: DataSource) -> dict:
    """Get column configuration for a specific source."""
    return COLUMN_CONFIG.get(source, COLUMN_CONFIG[DataSource.PRODUCT_HUNT])


def merge_sources(ph_products: list[dict], indie_products: list[dict]) -> list[dict]:
    """
    Merge products from multiple sources.
    Returns a unified list with source indicator.
    """
    all_products = []

    # Add Product Hunt products
    for p in ph_products:
        p["_source"] = "Product Hunt"
        all_products.append(p)

    # Add Indie Hackers products
    for p in indie_products:
        p["_source"] = "Indie Hackers"
        all_products.append(p)

    return all_products


def get_unified_columns() -> list[str]:
    """Get columns that exist in both sources for unified view."""
    return ["name", "tagline", "_source"]


def filter_products(
    products: list[dict],
    search: str = "",
    business_type: Optional[str] = None,
    verified_only: bool = False,
) -> list[dict]:
    """Filter products based on criteria."""
    filtered = products.copy()

    # Search filter
    if search:
        search_lower = search.lower()
        filtered = [
            p for p in filtered
            if search_lower in p.get("name", "").lower()
            or search_lower in p.get("tagline", "").lower()
        ]

    # Business type filter (Product Hunt only)
    if business_type and business_type != "All":
        filtered = [
            p for p in filtered
            if p.get("business_type") == business_type
        ]

    # Verified filter (Indie Hackers only)
    if verified_only:
        filtered = [
            p for p in filtered
            if p.get("stripe_verified", False)
        ]

    return filtered


def sort_products(
    products: list[dict],
    sort_by: str = "name",
    ascending: bool = True
) -> list[dict]:
    """Sort products by a given field."""
    if sort_by == "revenue":
        # Special handling for revenue sorting
        return sorted(
            products,
            key=lambda x: parse_revenue(x.get("revenue", "")),
            reverse=not ascending
        )

    return sorted(
        products,
        key=lambda x: x.get(sort_by, "") or "",
        reverse=not ascending
    )
