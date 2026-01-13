# -*- coding: utf-8 -*-
"""
Startup Scraper Dashboard - Main Entry Point
Multi-source product intelligence dashboard.
"""

import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Startup Scraper",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Startup Scraper Dashboard - Multi-source product intelligence"
    }
)

import sys
from pathlib import Path

# Add project root to path for imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import get_config
from database import init_database


# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #667eea;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Headers */
    h1 {
        color: #1a1a2e;
    }

    /* Success/Error badges */
    .badge-success {
        background-color: #28a745;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }

    .badge-b2b {
        background-color: #667eea;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }

    .badge-b2c {
        background-color: #f093fb;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }

    /* Source tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False

    if "selected_source" not in st.session_state:
        st.session_state.selected_source = "Product Hunt"

    if "indie_cache" not in st.session_state:
        st.session_state.indie_cache = []

    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = None


def init_db():
    """Initialize database connection."""
    if not st.session_state.db_initialized:
        try:
            config = get_config()
            init_database(config.supabase.url, config.supabase.key)
            st.session_state.db_initialized = True
            return True
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            return False
    return True


def main():
    """Main dashboard entry point."""
    init_session_state()

    # Sidebar
    with st.sidebar:
        st.image("https://em-content.zobj.net/source/apple/391/rocket_1f680.png", width=60)
        st.title("Startup Scraper")
        st.caption("Multi-source product intelligence")

        st.divider()

        # Source selector
        st.subheader("Data Source")
        source = st.radio(
            "Select source:",
            ["Product Hunt", "Indie Hackers", "All Sources"],
            index=["Product Hunt", "Indie Hackers", "All Sources"].index(
                st.session_state.selected_source
            ),
            key="source_selector"
        )
        st.session_state.selected_source = source

        st.divider()

        # Quick stats
        if init_db():
            from dashboard.utils.data import get_quick_stats
            stats = get_quick_stats()

            st.subheader("Quick Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total", stats.get("total", 0))
            with col2:
                st.metric("B2B", stats.get("b2b", 0))

        st.divider()

        # Footer
        st.caption("Built with Streamlit")
        st.caption("v1.0.0")

    # Main content - Welcome page
    st.title("🚀 Startup Scraper Dashboard")

    st.markdown("""
    Welcome to your **multi-source product intelligence dashboard**.

    Use the sidebar to navigate between pages:
    - **📊 Overview** - Key metrics and recent activity
    - **🔍 Explorer** - Browse and filter products
    - **📈 Analytics** - Charts and insights
    - **⚙️ Settings** - Configuration and scraping
    """)

    # Quick action cards
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("📊 **View Stats**\n\nSee database metrics and classification breakdown.")
        if st.button("Go to Overview", key="btn_overview"):
            st.switch_page("pages/1_📊_Overview.py")

    with col2:
        st.info("🔍 **Explore Products**\n\nBrowse, filter, and search all scraped products.")
        if st.button("Go to Explorer", key="btn_explorer"):
            st.switch_page("pages/2_🔍_Explorer.py")

    with col3:
        st.info("🚀 **Start Scraping**\n\nTrigger a new scrape from any source.")
        if st.button("Go to Settings", key="btn_settings"):
            st.switch_page("pages/4_⚙️_Settings.py")

    # Recent activity preview
    if init_db():
        st.subheader("Recent Products")

        from dashboard.utils.data import get_recent_products
        recent = get_recent_products(limit=5)

        if recent:
            for product in recent:
                with st.container():
                    cols = st.columns([3, 1, 1])
                    with cols[0]:
                        st.markdown(f"**{product.get('name', 'N/A')}**")
                        st.caption(product.get('tagline', '')[:80])
                    with cols[1]:
                        btype = product.get('business_type', 'UNKNOWN')
                        if btype == "B2B":
                            st.markdown('<span class="badge-b2b">B2B</span>', unsafe_allow_html=True)
                        elif btype == "B2C":
                            st.markdown('<span class="badge-b2c">B2C</span>', unsafe_allow_html=True)
                    with cols[2]:
                        st.caption(f"👍 {product.get('votes_count', 0)}")
        else:
            st.info("No products yet. Start scraping to populate your database!")


if __name__ == "__main__":
    main()
