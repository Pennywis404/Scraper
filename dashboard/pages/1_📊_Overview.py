# -*- coding: utf-8 -*-
"""
Overview Page - Key metrics and recent activity.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import get_config
from database import init_database

st.set_page_config(
    page_title="Overview - Startup Scraper",
    page_icon="📊",
    layout="wide"
)

# Initialize database
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


def render_metrics():
    """Render main metrics cards."""
    from dashboard.utils.data import get_quick_stats

    stats = get_quick_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📦 Total Products",
            value=stats.get("total", 0),
            help="Total products in database"
        )

    with col2:
        st.metric(
            label="🏢 B2B Products",
            value=stats.get("b2b", 0),
            delta=f"{(stats.get('b2b', 0) / max(stats.get('total', 1), 1) * 100):.0f}%"
        )

    with col3:
        st.metric(
            label="🛍️ B2C Products",
            value=stats.get("b2c", 0),
            delta=f"{(stats.get('b2c', 0) / max(stats.get('total', 1), 1) * 100):.0f}%"
        )

    with col4:
        st.metric(
            label="❓ Unclassified",
            value=stats.get("unknown", 0),
            delta=None if stats.get("unknown", 0) == 0 else "Needs review",
            delta_color="off"
        )


def render_classification_chart():
    """Render classification pie chart."""
    import plotly.express as px

    from dashboard.utils.data import get_quick_stats
    stats = get_quick_stats()

    # Pie chart data
    data = {
        "Type": ["B2B", "B2C", "Unknown"],
        "Count": [stats.get("b2b", 0), stats.get("b2c", 0), stats.get("unknown", 0)],
    }

    fig = px.pie(
        data,
        values="Count",
        names="Type",
        title="Classification Breakdown",
        color="Type",
        color_discrete_map={
            "B2B": "#667eea",
            "B2C": "#f093fb",
            "Unknown": "#e0e0e0"
        },
        hole=0.4  # Donut chart
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=40, b=40, l=20, r=20),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_recent_activity():
    """Render recent products table."""
    from dashboard.utils.data import get_recent_products

    products = get_recent_products(limit=10)

    if not products:
        st.info("No products found. Start scraping to populate your database!")
        return

    st.subheader("📋 Recent Products")

    for product in products:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.markdown(f"**{product.get('name', 'N/A')}**")
                tagline = product.get('tagline', '')
                if tagline:
                    st.caption(tagline[:100] + ("..." if len(tagline) > 100 else ""))

            with col2:
                btype = product.get("business_type", "UNKNOWN")
                if btype == "B2B":
                    st.success("🏢 B2B")
                elif btype == "B2C":
                    st.info("🛍️ B2C")
                else:
                    st.warning("❓ Unknown")

            with col3:
                votes = product.get("votes_count", 0)
                st.metric("Votes", votes)

            with col4:
                website = product.get("website", "")
                if website:
                    st.link_button("🔗 Visit", website)

        st.divider()


def render_top_voted():
    """Render top voted products."""
    from dashboard.utils.data import get_all_products, sort_products

    products = get_all_products()
    if not products:
        return

    # Sort by votes
    top_products = sort_products(products, "votes_count", ascending=False)[:5]

    st.subheader("🏆 Top Voted Products")

    for i, product in enumerate(top_products):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
        col1, col2, col3 = st.columns([0.5, 3, 1])

        with col1:
            st.markdown(f"### {medal}")

        with col2:
            st.markdown(f"**{product.get('name', 'N/A')}**")
            st.caption(product.get('tagline', '')[:60])

        with col3:
            st.metric("Votes", product.get("votes_count", 0))


def render_source_comparison():
    """Render source comparison if indie data available."""
    from dashboard.utils.data import get_all_products, get_indie_products

    ph_count = len(get_all_products())
    indie_products = get_indie_products(use_cache=True)
    indie_count = len(indie_products)

    if indie_count == 0:
        return

    st.subheader("📊 Source Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Product Hunt",
            ph_count,
            help="Products stored in Supabase"
        )

    with col2:
        st.metric(
            "Indie Hackers",
            indie_count,
            help="Products in session cache"
        )


def main():
    st.title("📊 Overview")
    st.caption("Key metrics and recent activity")

    if not init_db():
        return

    # Refresh button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    # Main metrics
    render_metrics()

    st.divider()

    # Two columns layout
    col_left, col_right = st.columns([2, 1])

    with col_left:
        render_recent_activity()

    with col_right:
        render_classification_chart()
        st.divider()
        render_top_voted()

    # Source comparison (if indie data available)
    render_source_comparison()


if __name__ == "__main__":
    main()
