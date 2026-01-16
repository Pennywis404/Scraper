# -*- coding: utf-8 -*-
"""CRM Page - Track contacted startups with editable table."""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database import ContactsRepository, LaunchesRepository, init_database
from config import get_config

# Initialize database
config = get_config()
init_database(config.supabase.url, config.supabase.key)

st.set_page_config(page_title="CRM", page_icon="📋", layout="wide")
st.title("📋 CRM - Base de Contacts")

# Initialize repositories
contacts_repo = ContactsRepository()
launches_repo = LaunchesRepository()

# Constants
CONTACT_METHODS = ["", "email", "linkedin", "instagram", "phone", "twitter", "other"]
STATUSES = ["to_contact", "contacted", "responded", "meeting", "not_interested", "converted"]
CONTACTED_BY = ["Théo", "Ethan"]

# Get all data
import asyncio
loop = asyncio.new_event_loop()
all_startups = loop.run_until_complete(launches_repo.get_all())
loop.close()

# Get existing contacts
existing_contacts = contacts_repo.get_all_contacts(limit=1000)
contacts_map = {c["startup_id"]: c for c in existing_contacts}

# Build DataFrame with all startups and their contact info
data = []
for startup in all_startups:
    contact = contacts_map.get(startup["id"], {})
    data.append({
        "startup_id": startup["id"],
        "name": startup.get("name", ""),
        "tagline": startup.get("tagline", "")[:80] if startup.get("tagline") else "",
        "website": startup.get("website", ""),
        "contact_method": contact.get("contact_method", ""),
        "contact_info": contact.get("contact_info", ""),
        "status": contact.get("status", "to_contact"),
        "contacted_by": contact.get("contacted_by", ""),
        "contacted_at": contact.get("contacted_at", None),
        "notes": contact.get("notes", ""),
    })

df = pd.DataFrame(data)

# Sidebar filters
st.sidebar.subheader("Filtres")

filter_status = st.sidebar.multiselect(
    "Statut",
    options=STATUSES,
    default=[]
)

filter_method = st.sidebar.multiselect(
    "Méthode de contact",
    options=[m for m in CONTACT_METHODS if m],
    default=[]
)

filter_person = st.sidebar.selectbox(
    "Contacté par",
    ["Tous", "Théo", "Ethan", "Non assigné"]
)

search_query = st.sidebar.text_input("Rechercher", placeholder="Nom de startup...")

# Apply filters
filtered_df = df.copy()

if filter_status:
    filtered_df = filtered_df[filtered_df["status"].isin(filter_status)]

if filter_method:
    filtered_df = filtered_df[filtered_df["contact_method"].isin(filter_method)]

if filter_person == "Non assigné":
    filtered_df = filtered_df[filtered_df["contacted_by"] == ""]
elif filter_person != "Tous":
    filtered_df = filtered_df[filtered_df["contacted_by"] == filter_person]

if search_query:
    filtered_df = filtered_df[
        filtered_df["name"].str.lower().str.contains(search_query.lower(), na=False) |
        filtered_df["tagline"].str.lower().str.contains(search_query.lower(), na=False)
    ]

# Stats
st.subheader("📊 Statistiques")
col1, col2, col3, col4, col5 = st.columns(5)

total_contacted = len(df[df["status"] != "to_contact"])
with col1:
    st.metric("Total scrappés", len(df))
with col2:
    st.metric("Contactés", total_contacted)
with col3:
    st.metric("En attente", len(df[df["status"] == "to_contact"]))
with col4:
    responses = len(df[df["status"].isin(["responded", "meeting", "converted"])])
    st.metric("Réponses", responses)
with col5:
    if total_contacted > 0:
        rate = round(responses / total_contacted * 100, 1)
        st.metric("Taux réponse", f"{rate}%")
    else:
        st.metric("Taux réponse", "0%")

st.divider()

# Instructions
with st.expander("ℹ️ Comment utiliser"):
    st.markdown("""
    **Ce tableau est éditable directement !**

    1. **Cliquez sur une cellule** pour la modifier
    2. **Méthode de contact** : Comment vous avez contacté (email, linkedin, instagram, phone...)
    3. **Contact Info** : Les coordonnées (adresse email, URL LinkedIn, @instagram, numéro...)
    4. **Statut** : L'état du contact
    5. Cliquez sur **💾 Sauvegarder** pour enregistrer vos modifications

    **Statuts :**
    - `to_contact` : À contacter
    - `contacted` : Message envoyé
    - `responded` : A répondu
    - `meeting` : RDV prévu
    - `not_interested` : Pas intéressé
    - `converted` : Client/Converti
    """)

# Editable table
st.subheader(f"📋 Contacts ({len(filtered_df)} affichés)")

# Configure column display
column_config = {
    "startup_id": None,  # Hidden
    "name": st.column_config.TextColumn(
        "Startup",
        width="medium",
        disabled=True
    ),
    "tagline": st.column_config.TextColumn(
        "Description",
        width="large",
        disabled=True
    ),
    "website": st.column_config.LinkColumn(
        "Website",
        width="small",
        disabled=True
    ),
    "contact_method": st.column_config.SelectboxColumn(
        "Via",
        options=CONTACT_METHODS,
        width="small"
    ),
    "contact_info": st.column_config.TextColumn(
        "Coordonnées",
        width="medium",
        help="Email, URL LinkedIn, @instagram, téléphone..."
    ),
    "status": st.column_config.SelectboxColumn(
        "Statut",
        options=STATUSES,
        width="small"
    ),
    "contacted_by": st.column_config.SelectboxColumn(
        "Par",
        options=["", "Théo", "Ethan"],
        width="small"
    ),
    "contacted_at": st.column_config.DateColumn(
        "Date",
        width="small"
    ),
    "notes": st.column_config.TextColumn(
        "Notes",
        width="medium"
    ),
}

# Display order
display_columns = ["name", "tagline", "website", "contact_method", "contact_info", "status", "contacted_by", "contacted_at", "notes", "startup_id"]

edited_df = st.data_editor(
    filtered_df[display_columns],
    column_config=column_config,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="crm_table"
)

# Save button
col_save, col_info = st.columns([1, 4])
with col_save:
    if st.button("💾 Sauvegarder les modifications", type="primary"):
        # Find changes and save
        changes = []
        for idx, row in edited_df.iterrows():
            original = filtered_df[filtered_df["startup_id"] == row["startup_id"]].iloc[0]

            # Check if anything changed
            if (row["contact_method"] != original["contact_method"] or
                row["contact_info"] != original["contact_info"] or
                row["status"] != original["status"] or
                row["contacted_by"] != original["contacted_by"] or
                str(row["contacted_at"]) != str(original["contacted_at"]) or
                row["notes"] != original["notes"]):

                changes.append({
                    "startup_id": row["startup_id"],
                    "contact_method": row["contact_method"] if row["contact_method"] else None,
                    "contact_info": row["contact_info"] if row["contact_info"] else None,
                    "status": row["status"],
                    "contacted_by": row["contacted_by"] if row["contacted_by"] else "Théo",
                    "contacted_at": row["contacted_at"] if pd.notna(row["contacted_at"]) else date.today(),
                    "notes": row["notes"] if row["notes"] else None,
                })

        if changes:
            contacts_repo.bulk_upsert_contacts(changes)
            st.success(f"✅ {len(changes)} contact(s) mis à jour!")
            st.rerun()
        else:
            st.info("Aucune modification détectée")

with col_info:
    st.caption("Les modifications sont enregistrées uniquement après avoir cliqué sur Sauvegarder")

# Sidebar legend
st.sidebar.divider()
st.sidebar.subheader("Légende Statuts")
st.sidebar.markdown("""
- 🔵 **to_contact** : À contacter
- 📤 **contacted** : Contacté
- 💬 **responded** : A répondu
- 📅 **meeting** : RDV prévu
- ❌ **not_interested** : Pas intéressé
- ✅ **converted** : Client
""")

st.sidebar.subheader("Méthodes de contact")
st.sidebar.markdown("""
- 📧 **email** : Email
- 💼 **linkedin** : LinkedIn
- 📸 **instagram** : Instagram
- 📞 **phone** : Téléphone
- 🐦 **twitter** : Twitter
- 📝 **other** : Autre
""")
