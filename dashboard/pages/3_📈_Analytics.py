# -*- coding: utf-8 -*-
"""
Analytics Page - Charts, insights, and data visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from collections import Counter

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import get_config
from database import init_database

st.set_page_config(
    page_title="Analytics - Startup Scraper",
    page_icon="📈",
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


def render_classification_analysis():
    """Render classification breakdown charts."""
    from dashboard.utils.data import get_quick_stats

    stats = get_quick_stats()

    col1, col2 = st.columns(2)

    with col1:
        # Pie chart
        fig = px.pie(
            values=[stats.get("b2b", 0), stats.get("b2c", 0), stats.get("unknown", 0)],
            names=["B2B", "B2C", "Unknown"],
            title="Classification Distribution",
            color_discrete_sequence=["#667eea", "#f093fb", "#e0e0e0"],
            hole=0.4
        )
        fig.update_layout(margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=["B2B", "B2C", "Unknown"],
                y=[stats.get("b2b", 0), stats.get("b2c", 0), stats.get("unknown", 0)],
                marker_color=["#667eea", "#f093fb", "#e0e0e0"],
                text=[stats.get("b2b", 0), stats.get("b2c", 0), stats.get("unknown", 0)],
                textposition="outside"
            )
        ])
        fig.update_layout(
            title="Product Counts by Type",
            yaxis_title="Count",
            margin=dict(t=50, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)


def render_votes_analysis():
    """Render votes distribution analysis."""
    from dashboard.utils.data import get_all_products

    products = get_all_products()
    if not products:
        st.info("No data available for votes analysis")
        return

    df = pd.DataFrame(products)

    if "votes_count" not in df.columns:
        return

    st.subheader("👍 Votes Distribution")

    col1, col2 = st.columns(2)

    with col1:
        # Histogram
        fig = px.histogram(
            df,
            x="votes_count",
            nbins=30,
            title="Votes Distribution",
            color_discrete_sequence=["#667eea"]
        )
        fig.update_layout(
            xaxis_title="Votes",
            yaxis_title="Number of Products",
            margin=dict(t=50, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Box plot by type
        if "business_type" in df.columns:
            fig = px.box(
                df,
                x="business_type",
                y="votes_count",
                title="Votes by Business Type",
                color="business_type",
                color_discrete_map={
                    "B2B": "#667eea",
                    "B2C": "#f093fb",
                    "UNKNOWN": "#e0e0e0"
                }
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(t=50, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Average Votes", f"{df['votes_count'].mean():.0f}")
    with col2:
        st.metric("Median Votes", f"{df['votes_count'].median():.0f}")
    with col3:
        st.metric("Max Votes", df['votes_count'].max())
    with col4:
        st.metric("Products > 100 votes", len(df[df['votes_count'] > 100]))


def render_topics_analysis():
    """Render topics/categories analysis."""
    from dashboard.utils.data import get_all_products

    products = get_all_products()
    if not products:
        return

    # Extract all topics
    all_topics = []
    for p in products:
        topics = p.get("topics", [])
        if isinstance(topics, list):
            all_topics.extend(topics)

    if not all_topics:
        st.info("No topics data available")
        return

    st.subheader("🏷️ Topics Analysis")

    # Count topics
    topic_counts = Counter(all_topics)
    top_topics = topic_counts.most_common(15)

    col1, col2 = st.columns(2)

    with col1:
        # Bar chart of top topics
        fig = px.bar(
            x=[t[1] for t in top_topics],
            y=[t[0] for t in top_topics],
            orientation='h',
            title="Top 15 Topics",
            color_discrete_sequence=["#667eea"]
        )
        fig.update_layout(
            xaxis_title="Count",
            yaxis_title="Topic",
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(t=50, b=20, l=100, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Treemap
        if len(top_topics) >= 5:
            fig = px.treemap(
                names=[t[0] for t in top_topics[:12]],
                parents=["" for _ in top_topics[:12]],
                values=[t[1] for t in top_topics[:12]],
                title="Topics Treemap"
            )
            fig.update_layout(margin=dict(t=50, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    # Total unique topics
    st.caption(f"Total unique topics: {len(topic_counts)}")


def render_indie_revenue_analysis():
    """Render Indie Hackers revenue analysis."""
    from dashboard.utils.data import get_indie_products, parse_revenue

    products = get_indie_products(use_cache=True)

    if not products:
        st.info("No Indie Hackers data in cache. Scrape from Settings page to see revenue analytics!")
        return

    st.subheader("💰 Indie Hackers Revenue Analysis")

    # Parse revenues
    revenue_data = []
    for p in products:
        revenue_str = p.get("revenue", "")
        revenue_num = parse_revenue(revenue_str)
        if revenue_num > 0:
            revenue_data.append({
                "name": p.get("name", "Unknown"),
                "revenue": revenue_num,
                "revenue_str": revenue_str,
                "verified": p.get("stripe_verified", False)
            })

    if not revenue_data:
        st.info("No revenue data available")
        return

    df = pd.DataFrame(revenue_data)

    col1, col2 = st.columns(2)

    with col1:
        # Revenue distribution
        fig = px.histogram(
            df,
            x="revenue",
            nbins=20,
            title="Revenue Distribution",
            color_discrete_sequence=["#28a745"]
        )
        fig.update_layout(
            xaxis_title="Monthly Revenue ($)",
            yaxis_title="Number of Products",
            margin=dict(t=50, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top revenue products
        top_revenue = df.nlargest(10, "revenue")

        fig = px.bar(
            top_revenue,
            x="revenue",
            y="name",
            orientation='h',
            title="Top 10 by Revenue",
            color="verified",
            color_discrete_map={True: "#28a745", False: "#6c757d"}
        )
        fig.update_layout(
            xaxis_title="Monthly Revenue ($)",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(t=50, b=20, l=100, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Average Revenue", f"${df['revenue'].mean():,.0f}/mo")
    with col2:
        st.metric("Median Revenue", f"${df['revenue'].median():,.0f}/mo")
    with col3:
        st.metric("Max Revenue", f"${df['revenue'].max():,.0f}/mo")
    with col4:
        verified_count = len(df[df['verified'] == True])
        st.metric("Stripe Verified", f"{verified_count}/{len(df)}")


def render_comparison_chart():
    """Render comparison between sources."""
    from dashboard.utils.data import get_all_products, get_indie_products

    ph_products = get_all_products()
    indie_products = get_indie_products(use_cache=True)

    if not ph_products and not indie_products:
        return

    st.subheader("📊 Source Comparison")

    col1, col2 = st.columns(2)

    with col1:
        # Product counts
        fig = go.Figure(data=[
            go.Bar(
                x=["Product Hunt", "Indie Hackers"],
                y=[len(ph_products), len(indie_products)],
                marker_color=["#da552f", "#4799eb"],
                text=[len(ph_products), len(indie_products)],
                textposition="outside"
            )
        ])
        fig.update_layout(
            title="Products by Source",
            yaxis_title="Count",
            margin=dict(t=50, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Source info
        st.markdown("### Source Details")

        st.markdown("**🏹 Product Hunt**")
        st.markdown(f"- Products: {len(ph_products)}")
        if ph_products:
            b2b = len([p for p in ph_products if p.get("business_type") == "B2B"])
            st.markdown(f"- B2B: {b2b} ({b2b/len(ph_products)*100:.0f}%)")
            avg_votes = sum(p.get("votes_count", 0) for p in ph_products) / len(ph_products)
            st.markdown(f"- Avg votes: {avg_votes:.0f}")

        st.markdown("---")

        st.markdown("**🚀 Indie Hackers**")
        st.markdown(f"- Products: {len(indie_products)}")
        if indie_products:
            from dashboard.utils.data import parse_revenue
            verified = len([p for p in indie_products if p.get("stripe_verified")])
            st.markdown(f"- Verified: {verified} ({verified/len(indie_products)*100:.0f}%)")
            revenues = [parse_revenue(p.get("revenue", "")) for p in indie_products]
            if revenues:
                avg_rev = sum(revenues) / len(revenues)
                st.markdown(f"- Avg revenue: ${avg_rev:,.0f}/mo")


def main():
    st.title("📈 Analytics")
    st.caption("Charts, insights, and data visualizations")

    if not init_db():
        return

    # Refresh button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Refresh"):
            st.cache_data.clear()
            st.rerun()

    # Analytics tabs
    tab1, tab2, tab3 = st.tabs(["📊 Classification", "🏹 Product Hunt", "🚀 Indie Hackers"])

    with tab1:
        render_classification_analysis()
        st.divider()
        render_comparison_chart()

    with tab2:
        render_votes_analysis()
        st.divider()
        render_topics_analysis()

    with tab3:
        render_indie_revenue_analysis()


if __name__ == "__main__":
    main()
