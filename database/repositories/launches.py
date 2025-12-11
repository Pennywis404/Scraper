from database.client import get_database
from scraper.models import Product, BusinessType


class LaunchesRepository:
    """Repository for Product Hunt launches in Supabase."""

    TABLE_NAME = "daily_launches"

    def __init__(self):
        self.db = get_database()

    async def insert_products(self, products: list[Product]) -> int:
        """Insert multiple products into the database. Returns count of inserted."""
        if not products:
            return 0

        # Deduplicate products by id (keep first occurrence)
        seen_ids = set()
        unique_products = []
        for p in products:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique_products.append(p)

        data = [p.to_dict() for p in unique_products]

        # Upsert to avoid duplicates (id = Product Hunt ID = PK)
        result = self.db.table(self.TABLE_NAME).upsert(
            data,
            on_conflict="id"
        ).execute()

        return len(result.data) if result.data else 0

    async def get_unclassified(self) -> list[dict]:
        """Get products that haven't been classified yet."""
        result = self.db.table(self.TABLE_NAME).select("*").eq(
            "business_type", BusinessType.UNKNOWN.value
        ).execute()

        return result.data if result.data else []

    async def update_classification(
        self,
        product_id: str,
        business_type: BusinessType,
        reason: str
    ) -> bool:
        """Update the classification of a product."""
        result = self.db.table(self.TABLE_NAME).update({
            "business_type": business_type.value,
            "classification_reason": reason,
        }).eq("id", product_id).execute()

        return len(result.data) > 0 if result.data else False

    async def get_b2b_products(self) -> list[dict]:
        """Get all products classified as B2B."""
        result = self.db.table(self.TABLE_NAME).select("*").eq(
            "business_type", BusinessType.B2B.value
        ).execute()

        return result.data if result.data else []

    async def get_all(self) -> list[dict]:
        """Get all products."""
        result = self.db.table(self.TABLE_NAME).select("*").execute()
        return result.data if result.data else []

    async def get_by_type(self, business_type: str) -> list[dict]:
        """Get products by business type (B2B, B2C, UNKNOWN)."""
        result = self.db.table(self.TABLE_NAME).select("*").eq(
            "business_type", business_type
        ).execute()
        return result.data if result.data else []

    async def get_stats(self) -> dict:
        """Get classification statistics."""
        all_products = await self.get_all()

        stats = {
            "total": len(all_products),
            "b2b": 0,
            "b2c": 0,
            "unknown": 0,
        }

        for p in all_products:
            bt = p.get("business_type", "UNKNOWN")
            if bt == "B2B":
                stats["b2b"] += 1
            elif bt == "B2C":
                stats["b2c"] += 1
            else:
                stats["unknown"] += 1

        return stats
