# -*- coding: utf-8 -*-
"""
Explorer Page - Browse and filter products with dynamic columns.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import get_config
from database import init_database, ContactsRepository
from datetime import date

st.set_page_config(
    page_title="Explorer - Startup Scraper",
    page_icon="🔍",
    layout="wide"
)


def get_contacts_repo():
    """Get or create contacts repository."""
    if "contacts_repo" not in st.session_state:
        st.session_state.contacts_repo = ContactsRepository()
    return st.session_state.contacts_repo


def render_contact_button(product_id: str, product_name: str, contacted_ids: set):
    """Render contact button for a product."""
    if product_id in contacted_ids:
        st.success("✅ Déjà contacté")
        return

    with st.popover("📞 Marquer comme contacté"):
        contacted_by = st.selectbox(
            "Par qui ?",
            ["Ethan", "Théo"],
            key=f"contact_by_{product_id}"
        )
        contact_method = st.selectbox(
            "Comment ?",
            ["email", "linkedin", "twitter", "other"],
            key=f"contact_method_{product_id}"
        )
        notes = st.text_input("Notes", key=f"contact_notes_{product_id}")

        if st.button("✅ Confirmer", key=f"confirm_contact_{product_id}"):
            repo = get_contacts_repo()
            repo.add_contact(
                startup_id=product_id,
                contacted_by=contacted_by,
                contacted_at=date.today(),
                contact_method=contact_method,
                notes=notes if notes else None
            )
            st.success(f"Contact enregistré pour {product_name}!")
            st.rerun()


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


def render_product_hunt_explorer():
    """Render Product Hunt products explorer."""
    from dashboard.utils.data import get_all_products, filter_products, sort_products

    # Filters in sidebar
    with st.sidebar:
        st.subheader("🔍 Filters")

        search = st.text_input("Search", placeholder="Product name...")

        business_type = st.selectbox(
            "Business Type",
            ["All", "B2B", "B2C", "UNKNOWN"]
        )

        sort_by = st.selectbox(
            "Sort by",
            ["votes_count", "comments_count", "name", "created_at"],
            format_func=lambda x: {
                "votes_count": "Votes",
                "comments_count": "Comments",
                "name": "Name",
                "created_at": "Date"
            }.get(x, x)
        )

        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

        min_votes = st.slider("Minimum votes", 0, 500, 0)

        contact_filter = st.selectbox(
            "Statut contact",
            ["Tous", "Non contactés", "Déjà contactés"],
            key="ph_contact_filter"
        )

    # Load and filter data
    products = get_all_products()

    if not products:
        st.info("No Product Hunt products found. Go to Settings to start scraping!")
        return

    # Apply filters
    filtered = filter_products(
        products,
        search=search,
        business_type=None if business_type == "All" else business_type
    )

    # Apply min votes filter
    if min_votes > 0:
        filtered = [p for p in filtered if p.get("votes_count", 0) >= min_votes]

    # Apply contact filter
    if contact_filter != "Tous":
        contacts_repo_filter = get_contacts_repo()
        contacted_ids_filter = contacts_repo_filter.get_contacted_startup_ids()
        if contact_filter == "Non contactés":
            filtered = [p for p in filtered if p.get("id") not in contacted_ids_filter]
        elif contact_filter == "Déjà contactés":
            filtered = [p for p in filtered if p.get("id") in contacted_ids_filter]

    # Sort
    filtered = sort_products(filtered, sort_by, ascending=(sort_order == "Ascending"))

    # Stats
    st.caption(f"Showing {len(filtered)} of {len(products)} products")

    # Convert to DataFrame for display
    if filtered:
        df = pd.DataFrame(filtered)

        # Select and rename columns
        display_columns = ["name", "tagline", "business_type", "votes_count", "comments_count", "created_at", "website"]
        available_cols = [c for c in display_columns if c in df.columns]
        df_display = df[available_cols].copy()

        # Rename columns for display
        df_display.columns = ["Name", "Tagline", "Type", "Votes", "Comments", "Date", "Website"][:len(available_cols)]

        # Display table
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Tagline": st.column_config.TextColumn("Tagline", width="large"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Votes": st.column_config.NumberColumn("👍 Votes", width="small"),
                "Comments": st.column_config.NumberColumn("💬 Comments", width="small"),
                "Date": st.column_config.DatetimeColumn("📅 Date", width="small", format="DD/MM/YYYY"),
                "Website": st.column_config.LinkColumn("🔗 Website", width="medium"),
            }
        )

        # Expandable product details
        st.subheader("📋 Product Details")

        # Get contacted IDs for badge display
        contacts_repo = get_contacts_repo()
        contacted_ids = contacts_repo.get_contacted_startup_ids()

        for product in filtered[:20]:  # Limit to avoid performance issues
            product_id = product.get("id", "")
            is_contacted = product_id in contacted_ids
            contact_badge = " ✅" if is_contacted else ""
            with st.expander(f"{product.get('name', 'N/A')} - {product.get('business_type', 'N/A')}{contact_badge}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**{product.get('name', 'N/A')}**")
                    st.markdown(f"_{product.get('tagline', '')}_")

                    if product.get("description"):
                        st.markdown("**Description:**")
                        st.markdown(product.get("description", "")[:500])

                    if product.get("topics"):
                        topics = product.get("topics", [])
                        if topics:
                            st.markdown("**Topics:** " + ", ".join(topics[:5]))

                with col2:
                    st.metric("Votes", product.get("votes_count", 0))
                    st.metric("Comments", product.get("comments_count", 0))

                    if product.get("maker_name"):
                        st.markdown(f"**Maker:** {product.get('maker_name')}")

                    if product.get("website"):
                        st.link_button("🔗 Visit Website", product.get("website"))

                    if product.get("url"):
                        st.link_button("🏹 Product Hunt", product.get("url"))

                    # Classification reason
                    if product.get("classification_reason"):
                        st.info(f"**Why {product.get('business_type')}:** {product.get('classification_reason')}")

                # Contact button
                st.divider()
                render_contact_button(product_id, product.get('name', 'N/A'), contacted_ids)


def render_indie_hackers_explorer():
    """Render Indie Hackers products explorer."""
    from dashboard.utils.data import get_indie_products, filter_products, sort_products, parse_revenue

    # Filters in sidebar
    with st.sidebar:
        st.subheader("🔍 Filters")

        search = st.text_input("Search", placeholder="Product name...", key="indie_search")

        verified_only = st.checkbox("Stripe verified only", value=False)

        sort_by = st.selectbox(
            "Sort by",
            ["revenue", "name", "scraped_at"],
            format_func=lambda x: {"revenue": "Revenue", "name": "Name", "scraped_at": "Date"}.get(x, x),
            key="indie_sort"
        )

        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True, key="indie_order")

    # Load data
    products = get_indie_products(use_cache=True)

    if not products:
        st.warning("No Indie Hackers data found. Go to Settings to scrape fresh data!")
        return

    # Apply filters
    filtered = filter_products(
        products,
        search=search,
        verified_only=verified_only
    )

    # Sort
    filtered = sort_products(filtered, sort_by, ascending=(sort_order == "Ascending"))

    # Stats
    st.caption(f"Showing {len(filtered)} of {len(products)} products")

    # Convert to DataFrame
    if filtered:
        df = pd.DataFrame(filtered)

        # Select columns for Indie Hackers
        display_columns = ["name", "tagline", "revenue", "stripe_verified", "url"]
        available_cols = [c for c in display_columns if c in df.columns]
        df_display = df[available_cols].copy()

        # Add revenue numeric for sorting display
        if "revenue" in df_display.columns:
            df_display["_revenue_num"] = df_display["revenue"].apply(parse_revenue)

        # Rename columns
        col_names = ["Name", "Tagline", "Revenue", "Verified", "Link"][:len(available_cols)]
        df_display.columns = col_names + (["_rev"] if "revenue" in display_columns else [])

        # Display
        st.dataframe(
            df_display[[c for c in df_display.columns if not c.startswith("_")]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Tagline": st.column_config.TextColumn("Tagline", width="large"),
                "Revenue": st.column_config.TextColumn("💰 Revenue", width="small"),
                "Verified": st.column_config.CheckboxColumn("✅ Verified", width="small"),
                "Link": st.column_config.LinkColumn("🔗 Link", width="medium"),
            }
        )

        # Product cards
        st.subheader("🚀 Product Cards")

        cols = st.columns(2)
        for i, product in enumerate(filtered[:20]):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"### {product.get('name', 'N/A')}")
                    st.caption(product.get('tagline', ''))

                    col1, col2 = st.columns(2)
                    with col1:
                        revenue = product.get("revenue", "N/A")
                        st.metric("Revenue", revenue)

                    with col2:
                        verified = "✅ Yes" if product.get("stripe_verified") else "❌ No"
                        st.metric("Stripe Verified", verified)

                    if product.get("url"):
                        st.link_button("View on Indie Hackers", product.get("url"), use_container_width=True)

                    st.divider()


def render_all_sources_explorer():
    """Render combined explorer for all sources."""
    from dashboard.utils.data import get_all_products, get_indie_products, merge_sources, filter_products

    # Load both sources
    ph_products = get_all_products()
    indie_products = get_indie_products(use_cache=True)

    # Merge
    all_products = merge_sources(ph_products, indie_products)

    if not all_products:
        st.info("No products found. Go to Settings to start scraping!")
        return

    # Filters
    with st.sidebar:
        st.subheader("🔍 Filters")

        search = st.text_input("Search", placeholder="Product name...", key="all_search")

        source_filter = st.multiselect(
            "Sources",
            ["Product Hunt", "Indie Hackers"],
            default=["Product Hunt", "Indie Hackers"]
        )

    # Apply source filter
    filtered = [p for p in all_products if p.get("_source") in source_filter]

    # Apply search
    filtered = filter_products(filtered, search=search)

    # Stats
    st.caption(f"Showing {len(filtered)} products from {len(source_filter)} source(s)")

    # Group by source
    ph_filtered = [p for p in filtered if p.get("_source") == "Product Hunt"]
    indie_filtered = [p for p in filtered if p.get("_source") == "Indie Hackers"]

    # Tabs for each source
    tab1, tab2 = st.tabs([f"🏹 Product Hunt ({len(ph_filtered)})", f"🚀 Indie Hackers ({len(indie_filtered)})"])

    with tab1:
        if ph_filtered:
            for product in ph_filtered[:15]:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{product.get('name', 'N/A')}**")
                        st.caption(product.get('tagline', '')[:80])
                    with col2:
                        btype = product.get("business_type", "UNKNOWN")
                        st.caption(f"Type: {btype}")
                    with col3:
                        st.caption(f"👍 {product.get('votes_count', 0)}")
                    st.divider()
        else:
            st.info("No Product Hunt products match your filters")

    with tab2:
        if indie_filtered:
            for product in indie_filtered[:15]:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{product.get('name', 'N/A')}**")
                        st.caption(product.get('tagline', '')[:80])
                    with col2:
                        st.caption(product.get('revenue', 'N/A'))
                    with col3:
                        verified = "✅" if product.get("stripe_verified") else "❌"
                        st.caption(f"Verified: {verified}")
                    st.divider()
        else:
            st.info("No Indie Hackers products in cache. Scrape from Settings page!")


def main():
    st.title("🔍 Explorer")
    st.caption("Browse and filter products from all sources")

    if not init_db():
        return

    # Source selector
    if "selected_source" not in st.session_state:
        st.session_state.selected_source = "Product Hunt"

    source = st.radio(
        "Select data source:",
        ["Product Hunt", "Indie Hackers", "All Sources"],
        horizontal=True,
        key="explorer_source"
    )

    st.divider()

    # Render appropriate explorer
    if source == "Product Hunt":
        render_product_hunt_explorer()
    elif source == "Indie Hackers":
        render_indie_hackers_explorer()
    else:
        render_all_sources_explorer()


if __name__ == "__main__":
    main()
