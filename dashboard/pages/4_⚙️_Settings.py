# -*- coding: utf-8 -*-
"""
Settings Page - Configuration and scraping controls.
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import get_config
from database import init_database

st.set_page_config(
    page_title="Settings - Startup Scraper",
    page_icon="⚙️",
    layout="wide"
)


def init_db():
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False
    if not st.session_state.db_initialized:
        try:
            config = get_config()
            init_database(config.supabase.url, config.supabase.key)
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"Database error: {e}")
            return False
    return True


def run_async(coro):
    """Run async function synchronously."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def render_scraping_controls():
    """Render scraping controls section."""
    st.subheader("🔄 Scraping Controls")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏹 Product Hunt")
        st.markdown("Scrape from Product Hunt API → Store in Supabase → Classify with AI")

        ph_limit = st.number_input(
            "Number of products",
            min_value=5,
            max_value=200,
            value=50,
            step=5,
            key="ph_limit"
        )

        if st.button("🚀 Start Product Hunt Scrape", key="btn_ph_scrape", use_container_width=True):
            scrape_product_hunt(ph_limit)

    with col2:
        st.markdown("### 🚀 Indie Hackers")
        st.markdown("Scrape from Indie Hackers website → Store in Supabase → Classify with AI")

        indie_limit = st.number_input(
            "Number of products",
            min_value=5,
            max_value=100,
            value=30,
            step=5,
            key="indie_limit"
        )

        if st.button("🚀 Start Indie Hackers Scrape", key="btn_indie_scrape", use_container_width=True):
            scrape_indie_hackers(indie_limit)

    # Last scrape info
    st.divider()

    if st.session_state.get("last_indie_scrape"):
        st.info(f"Last Indie Hackers scrape: {st.session_state.last_indie_scrape.strftime('%Y-%m-%d %H:%M')}")

    if st.session_state.get("indie_cache"):
        st.success(f"Indie Hackers cache: {len(st.session_state.indie_cache)} products")


def scrape_product_hunt(limit: int):
    """Run Product Hunt scraping workflow."""
    from database.repositories.launches import LaunchesRepository
    from scraper import ProductHuntClient
    from agents import WorkflowSupervisor, ClassifierAgent, GoogleSheetsExporter

    progress = st.progress(0, text="Initializing...")

    try:
        config = get_config()

        progress.progress(10, text="Connecting to Product Hunt API...")

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

        status_placeholder = st.empty()

        def update_status(message: str):
            status_placeholder.info(f"⏳ {message}")

        supervisor = WorkflowSupervisor(
            scraper=scraper,
            repository=repository,
            classifier=classifier,
            sheets_exporter=sheets_exporter,
            on_status=update_status,
        )

        progress.progress(30, text="Scraping products...")

        stats = run_async(supervisor.run(
            limit=limit,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
        ))

        run_async(scraper.close())

        progress.progress(100, text="Complete!")

        # Show results
        st.success("Scraping complete!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Products Scraped", stats.get("scraped", 0))
        with col2:
            st.metric("Stored in DB", stats.get("stored", 0))
        with col3:
            st.metric("Classified", stats.get("classified", 0))

        # Clear cache to refresh data
        st.cache_data.clear()

    except Exception as e:
        progress.empty()
        st.error(f"Scraping failed: {e}")


def scrape_indie_hackers(limit: int):
    """Run Indie Hackers scraping with DB persistence and classification."""
    from scraper.indiehackers import IndieHackersClient
    from database.repositories.indie import IndieProductsRepository
    from agents import ClassifierAgent

    progress = st.progress(0, text="Launching browser...")

    try:
        config = get_config()

        # Step 1: Scrape
        async def do_scrape():
            client = IndieHackersClient(headless=True)
            try:
                products = await client.get_products(limit=limit)
                return products  # Return IndieProduct objects
            finally:
                await client.close()

        progress.progress(20, text="Scraping products...")
        products = run_async(do_scrape())

        progress.progress(40, text="Storing in database...")

        # Step 2: Store in Supabase
        indie_repo = IndieProductsRepository()
        stored = run_async(indie_repo.insert_products(products))

        progress.progress(50, text="Classifying products...")

        # Step 3: Classify unclassified products
        classifier = ClassifierAgent(api_key=config.groq.api_key)
        unclassified = run_async(indie_repo.get_unclassified())

        b2b_count = 0
        b2c_count = 0

        for i, product in enumerate(unclassified):
            progress.progress(
                50 + int(40 * (i + 1) / max(len(unclassified), 1)),
                text=f"Classifying {i+1}/{len(unclassified)}..."
            )
            business_type, reason = run_async(classifier.classify(
                name=product.get("name", ""),
                tagline=product.get("tagline", ""),
                description=product.get("tagline", ""),
            ))
            run_async(indie_repo.update_classification(
                product.get("id"), business_type, reason
            ))
            if business_type.value == "B2B":
                b2b_count += 1
            elif business_type.value == "B2C":
                b2c_count += 1

        # Convert to dicts for cache
        products_dict = [p.to_dict() if hasattr(p, 'to_dict') else p for p in products]

        # Add source field
        for p in products_dict:
            p["_source"] = "Indie Hackers"

        # Update session cache (bonus for fast display)
        st.session_state.indie_cache = products_dict
        st.session_state.last_indie_scrape = datetime.now()

        progress.progress(100, text="Complete!")

        st.success(f"Scraped {len(products)} products from Indie Hackers!")

        # Show detailed results
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Scraped", len(products))
        with col2:
            st.metric("Stored", stored)
        with col3:
            st.metric("B2B", b2b_count)
        with col4:
            st.metric("B2C", b2c_count)

        # Show preview
        if products_dict:
            st.markdown("### Preview (Top 5)")
            for p in products_dict[:5]:
                verified = "✅" if p.get("stripe_verified") else ""
                btype = p.get("business_type", "UNKNOWN")
                st.markdown(f"- **{p.get('name')}** [{btype}] - {p.get('revenue', 'N/A')} {verified}")

        # Clear cache to refresh data in other pages
        st.cache_data.clear()

    except Exception as e:
        progress.empty()
        st.error(f"Scraping failed: {e}")


def render_export_controls():
    """Render export controls section."""
    st.subheader("📤 Export")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Export to Google Sheets")

        if st.button("📊 Export Product Hunt B2B", use_container_width=True):
            export_to_sheets("b2b")

        if st.button("📊 Export All Products", use_container_width=True):
            export_to_sheets("all")

    with col2:
        st.markdown("### Export Indie Hackers")

        if st.session_state.get("indie_cache"):
            if st.button("📊 Export Indie to Sheets", use_container_width=True):
                export_indie_to_sheets()
        else:
            st.info("Scrape Indie Hackers first to enable export")


def export_to_sheets(export_type: str):
    """Export products to Google Sheets."""
    from agents import GoogleSheetsExporter
    from dashboard.utils.data import get_all_products, get_products_by_type

    try:
        config = get_config()

        if export_type == "b2b":
            products = get_products_by_type("B2B")
        else:
            products = get_all_products()

        if not products:
            st.warning("No products to export")
            return

        sheets_exporter = GoogleSheetsExporter(
            credentials=config.google_sheets.credentials,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
        )

        # Convert to Product objects for the exporter
        from scraper.models import Product, BusinessType

        product_objs = []
        for p in products:
            product_objs.append(Product(
                id=p.get("id", ""),
                name=p.get("name", ""),
                tagline=p.get("tagline", ""),
                description=p.get("description", ""),
                url=p.get("url", ""),
                website=p.get("website"),
                votes_count=p.get("votes_count", 0),
                comments_count=p.get("comments_count", 0),
                topics=p.get("topics", []),
                maker_name=p.get("maker_name"),
                business_type=BusinessType(p.get("business_type", "UNKNOWN")),
                classification_reason=p.get("classification_reason"),
            ))

        worksheet = "B2B Products" if export_type == "b2b" else "All Products"
        count = sheets_exporter.export_b2b_products(
            product_objs,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
            worksheet_name=worksheet
        )

        st.success(f"Exported {count} products to '{worksheet}' sheet!")

    except Exception as e:
        st.error(f"Export failed: {e}")


def export_indie_to_sheets():
    """Export Indie Hackers cache to Google Sheets."""
    from agents import GoogleSheetsExporter
    from scraper.indiehackers import IndieProduct

    try:
        config = get_config()
        products = st.session_state.get("indie_cache", [])

        if not products:
            st.warning("No Indie products in cache")
            return

        # Convert to IndieProduct objects
        product_objs = [
            IndieProduct(
                name=p.get("name", ""),
                tagline=p.get("tagline", ""),
                revenue=p.get("revenue", ""),
                url=p.get("url", ""),
                stripe_verified=p.get("stripe_verified", False),
            )
            for p in products
        ]

        sheets_exporter = GoogleSheetsExporter(
            credentials=config.google_sheets.credentials,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
        )

        count = sheets_exporter.export_indie_products(
            product_objs,
            spreadsheet_id=config.google_sheets.spreadsheet_id,
        )

        st.success(f"Exported {count} products to 'Indie Hackers' sheet!")

    except Exception as e:
        st.error(f"Export failed: {e}")


def render_cache_management():
    """Render cache management section."""
    st.subheader("🗑️ Cache Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Clear Data Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Data cache cleared!")

    with col2:
        if st.button("Clear Indie Cache", use_container_width=True):
            st.session_state.indie_cache = []
            st.session_state.pop("last_indie_scrape", None)
            st.success("Indie Hackers cache cleared!")

    with col3:
        if st.button("Clear All Caches", use_container_width=True):
            st.cache_data.clear()
            st.session_state.indie_cache = []
            st.session_state.pop("last_indie_scrape", None)
            st.success("All caches cleared!")


def render_connection_status():
    """Render connection status section."""
    st.subheader("🔗 Connection Status")

    try:
        config = get_config()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Supabase**")
            if config.supabase.url and config.supabase.key:
                st.success("✅ Configured")
            else:
                st.error("❌ Missing credentials")

        with col2:
            st.markdown("**Product Hunt API**")
            if config.product_hunt.api_token:
                st.success("✅ Configured")
            else:
                st.error("❌ Missing token")

        with col3:
            st.markdown("**Google Sheets**")
            if config.google_sheets.credentials:
                st.success("✅ Configured")
            else:
                st.error("❌ Missing credentials")

        # Groq for classification
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Groq API (Classification)**")
            if config.groq.api_key:
                st.success("✅ Configured")
            else:
                st.warning("⚠️ Missing - Classification disabled")

        with col2:
            st.markdown("**Spreadsheet ID**")
            if config.google_sheets.spreadsheet_id:
                st.info(f"📋 {config.google_sheets.spreadsheet_id[:20]}...")
            else:
                st.warning("⚠️ Not set")

    except Exception as e:
        st.error(f"Error checking configuration: {e}")


def main():
    st.title("⚙️ Settings")
    st.caption("Configuration and scraping controls")

    if not init_db():
        pass  # Continue anyway to show settings

    # Sections
    render_connection_status()

    st.divider()

    render_scraping_controls()

    st.divider()

    render_export_controls()

    st.divider()

    render_cache_management()

    # Info section
    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Startup Scraper Dashboard** v1.0.0

    Multi-source product intelligence platform:
    - 🏹 **Product Hunt**: API scraping with B2B/B2C classification
    - 🚀 **Indie Hackers**: Web scraping with revenue tracking

    Built with Streamlit, Supabase, and Playwright.
    """)


if __name__ == "__main__":
    main()
