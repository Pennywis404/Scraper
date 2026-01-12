"""Repository for startup contacts (CRM)."""

from typing import Optional, List
from datetime import date
from database.client import get_database


class ContactsRepository:
    """Repository for managing startup contacts."""

    TABLE = "startup_contacts"

    def __init__(self):
        self.db = get_database()

    def add_contact(
        self,
        startup_id: str,
        contacted_by: str,
        contacted_at: Optional[date] = None,
        contact_method: Optional[str] = None,
        notes: Optional[str] = None,
        status: str = "contacted"
    ) -> dict:
        """Add a new contact record for a startup."""
        data = {
            "startup_id": startup_id,
            "contacted_by": contacted_by,
            "status": status,
        }
        if contacted_at:
            data["contacted_at"] = contacted_at.isoformat()
        if contact_method:
            data["contact_method"] = contact_method
        if notes:
            data["notes"] = notes

        result = self.db.table(self.TABLE).upsert(data, on_conflict="startup_id").execute()
        return result.data[0] if result.data else {}

    def update_contact(self, startup_id: str, **fields) -> dict:
        """Update an existing contact record."""
        if "contacted_at" in fields and isinstance(fields["contacted_at"], date):
            fields["contacted_at"] = fields["contacted_at"].isoformat()

        result = (
            self.db.table(self.TABLE)
            .update(fields)
            .eq("startup_id", startup_id)
            .execute()
        )
        return result.data[0] if result.data else {}

    def get_contact(self, startup_id: str) -> Optional[dict]:
        """Get contact record for a startup."""
        result = (
            self.db.table(self.TABLE)
            .select("*")
            .eq("startup_id", startup_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def delete_contact(self, startup_id: str) -> bool:
        """Delete a contact record."""
        result = (
            self.db.table(self.TABLE)
            .delete()
            .eq("startup_id", startup_id)
            .execute()
        )
        return len(result.data) > 0

    def get_all_contacts(
        self,
        contacted_by: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """Get all contacts with optional filters."""
        query = (
            self.db.table(self.TABLE)
            .select("*, daily_launches(*)")
            .order("contacted_at", desc=True)
            .limit(limit)
        )

        if contacted_by:
            query = query.eq("contacted_by", contacted_by)
        if status:
            query = query.eq("status", status)

        result = query.execute()
        return result.data

    def get_contacts_stats(self) -> dict:
        """Get contact statistics."""
        all_contacts = self.db.table(self.TABLE).select("contacted_by, status").execute()

        stats = {
            "total": len(all_contacts.data),
            "by_person": {"Ethan": 0, "Théo": 0},
            "by_status": {}
        }

        for contact in all_contacts.data:
            # By person
            person = contact.get("contacted_by")
            if person in stats["by_person"]:
                stats["by_person"][person] += 1

            # By status
            status = contact.get("status", "contacted")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        return stats

    def get_contacted_startup_ids(self) -> set:
        """Get set of all contacted startup IDs."""
        result = self.db.table(self.TABLE).select("startup_id").execute()
        return {r["startup_id"] for r in result.data}
