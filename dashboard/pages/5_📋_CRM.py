# -*- coding: utf-8 -*-
"""CRM Page - Track contacted startups."""

import streamlit as st
import sys
from pathlib import Path
from datetime import date, datetime

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database import ContactsRepository, LaunchesRepository, init_database
from config import get_config

# Initialize database
config = get_config()
init_database(config.supabase.url, config.supabase.key)

st.title("📋 CRM - Suivi des Contacts")

# Initialize repositories
contacts_repo = ContactsRepository()
launches_repo = LaunchesRepository()

# Sidebar filters
st.sidebar.subheader("Filtres")

filter_person = st.sidebar.selectbox(
    "Contacté par",
    ["Tous", "Ethan", "Théo"]
)

filter_status = st.sidebar.selectbox(
    "Statut",
    ["Tous", "to_contact", "contacted", "responded", "meeting", "not_interested", "converted"]
)

# Stats
st.subheader("📊 Statistiques")
stats = contacts_repo.get_contacts_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total contactés", stats["total"])
with col2:
    st.metric("Par Ethan", stats["by_person"].get("Ethan", 0))
with col3:
    st.metric("Par Théo", stats["by_person"].get("Théo", 0))
with col4:
    responded = stats["by_status"].get("responded", 0) + stats["by_status"].get("meeting", 0) + stats["by_status"].get("converted", 0)
    st.metric("Réponses", responded)

st.divider()

# Tabs
tab1, tab2 = st.tabs(["📋 Contacts", "➕ Nouveau contact"])

# Tab 1: List of contacts
with tab1:
    # Get contacts with filters
    contacted_by = None if filter_person == "Tous" else filter_person
    status = None if filter_status == "Tous" else filter_status

    contacts = contacts_repo.get_all_contacts(
        contacted_by=contacted_by,
        status=status,
        limit=200
    )

    if not contacts:
        st.info("Aucun contact enregistré avec ces filtres.")
    else:
        st.write(f"**{len(contacts)} contacts trouvés**")

        for contact in contacts:
            startup = contact.get("daily_launches", {})
            startup_name = startup.get("name", "N/A") if startup else "N/A"
            startup_tagline = startup.get("tagline", "") if startup else ""
            startup_website = startup.get("website", "") if startup else ""

            with st.expander(f"**{startup_name}** - {contact.get('status', 'contacted')}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.write(f"📝 {startup_tagline[:100]}" if startup_tagline else "")
                    if startup_website:
                        st.write(f"🔗 [{startup_website}]({startup_website})")
                    if contact.get("notes"):
                        st.write(f"💬 **Notes:** {contact['notes']}")

                with col2:
                    st.write(f"👤 **Par:** {contact.get('contacted_by', 'N/A')}")
                    st.write(f"📅 **Date:** {contact.get('contacted_at', 'N/A')}")
                    st.write(f"📧 **Via:** {contact.get('contact_method', 'N/A')}")

                # Update status
                st.write("---")
                col_status, col_notes, col_save = st.columns([1, 2, 1])

                with col_status:
                    new_status = st.selectbox(
                        "Statut",
                        ["to_contact", "contacted", "responded", "meeting", "not_interested", "converted"],
                        index=["to_contact", "contacted", "responded", "meeting", "not_interested", "converted"].index(contact.get("status", "contacted")),
                        key=f"status_{contact['startup_id']}"
                    )

                with col_notes:
                    new_notes = st.text_input(
                        "Notes",
                        value=contact.get("notes", "") or "",
                        key=f"notes_{contact['startup_id']}"
                    )

                with col_save:
                    st.write("")  # Spacing
                    if st.button("💾 Sauvegarder", key=f"save_{contact['startup_id']}"):
                        contacts_repo.update_contact(
                            contact["startup_id"],
                            status=new_status,
                            notes=new_notes
                        )
                        st.success("Mis à jour!")
                        st.rerun()

                # Delete button
                if st.button("🗑️ Supprimer ce contact", key=f"delete_{contact['startup_id']}"):
                    contacts_repo.delete_contact(contact["startup_id"])
                    st.success("Contact supprimé!")
                    st.rerun()

# Tab 2: Add new contact
with tab2:
    st.subheader("Ajouter un nouveau contact")

    # Get startups not yet contacted
    contacted_ids = contacts_repo.get_contacted_startup_ids()
    # Get all startups (synchronous wrapper needed)
    import asyncio
    loop = asyncio.new_event_loop()
    all_startups = loop.run_until_complete(launches_repo.get_all())
    loop.close()
    available_startups = [s for s in all_startups if s["id"] not in contacted_ids]

    if not available_startups:
        st.warning("Toutes les startups ont déjà été contactées!")
    else:
        # Search/Select startup
        startup_options = {f"{s['name']} - {s.get('tagline', '')[:50]}": s["id"] for s in available_startups}

        selected_startup = st.selectbox(
            "Sélectionner une startup",
            options=list(startup_options.keys()),
            key="new_contact_startup"
        )

        col1, col2 = st.columns(2)

        with col1:
            contacted_by = st.selectbox(
                "Contacté par",
                ["Ethan", "Théo"],
                key="new_contact_by"
            )

            contact_method = st.selectbox(
                "Méthode de contact",
                ["email", "linkedin", "twitter", "other"],
                key="new_contact_method"
            )

        with col2:
            contacted_at = st.date_input(
                "Date du contact",
                value=date.today(),
                key="new_contact_date"
            )

            status = st.selectbox(
                "Statut",
                ["contacted", "to_contact", "responded", "meeting", "not_interested", "converted"],
                key="new_contact_status"
            )

        notes = st.text_area(
            "Notes",
            placeholder="Ajouter des notes sur ce contact...",
            key="new_contact_notes"
        )

        if st.button("✅ Enregistrer le contact", type="primary"):
            startup_id = startup_options[selected_startup]

            contacts_repo.add_contact(
                startup_id=startup_id,
                contacted_by=contacted_by,
                contacted_at=contacted_at,
                contact_method=contact_method,
                notes=notes if notes else None,
                status=status
            )

            st.success(f"Contact enregistré pour {selected_startup.split(' - ')[0]}!")
            st.balloons()
            st.rerun()

# Status legend
st.sidebar.divider()
st.sidebar.subheader("Légende des statuts")
st.sidebar.markdown("""
- **to_contact**: À contacter
- **contacted**: Contacté
- **responded**: A répondu
- **meeting**: RDV prévu
- **not_interested**: Pas intéressé
- **converted**: Converti/Client
""")
