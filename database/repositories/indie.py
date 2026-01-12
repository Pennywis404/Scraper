# -*- coding: utf-8 -*-
"""Repository for Indie Hackers products in Supabase."""

import hashlib
from database.client import get_database
from scraper.models import BusinessType


def _generate_id(url: str) -> str:
    """Generate a unique ID from the URL."""
    return hashlib.md5(url.encode()).hexdigest()[:16]


class IndieProductsRepository:
    """Repository for Indie Hackers products in Supabase."""

    TABLE_NAME = "indie_products"

    def __init__(self):
        self.db = get_database()

    async def insert_products(self, products: list) -> int:
        """
        Insert multiple Indie Hackers products into the database.
        Products can be IndieProduct objects or dicts.
        Returns count of inserted/updated.
        """
        if not products:
            return 0

        # Convert to dicts and add IDs
        data = []
        seen_urls = set()

        for p in products:
            # Handle both IndieProduct objects and dicts
            if hasattr(p, 'to_dict'):
                product_dict = p.to_dict()
            else:
                product_dict = p

            url = product_dict.get("url", "")
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            # Generate ID from URL
            product_dict["id"] = _generate_id(url)

            # Ensure business_type exists
            if "business_type" not in product_dict:
                product_dict["business_type"] = "UNKNOWN"

            data.append(product_dict)

        if not data:
            return 0

        # Upsert to avoid duplicates
        result = self.db.table(self.TABLE_NAME).upsert(
            data,
            on_conflict="id"
        ).execute()

        return len(result.data) if result.data else 0

    async def get_all(self) -> list[dict]:
        """Get all Indie Hackers products."""
        result = self.db.table(self.TABLE_NAME).select("*").order(
            "scraped_at", desc=True
        ).execute()
        return result.data if result.data else []

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

    async def get_by_type(self, business_type: str) -> list[dict]:
        """Get products by business type (B2B, B2C, UNKNOWN)."""
        result = self.db.table(self.TABLE_NAME).select("*").eq(
            "business_type", business_type
        ).order("scraped_at", desc=True).execute()
        return result.data if result.data else []

    async def get_verified_only(self) -> list[dict]:
        """Get only Stripe-verified products."""
        result = self.db.table(self.TABLE_NAME).select("*").eq(
            "stripe_verified", True
        ).order("scraped_at", desc=True).execute()
        return result.data if result.data else []

    async def get_stats(self) -> dict:
        """Get statistics for Indie Hackers products."""
        all_products = await self.get_all()

        stats = {
            "total": len(all_products),
            "b2b": 0,
            "b2c": 0,
            "unknown": 0,
            "verified": 0,
        }

        for p in all_products:
            bt = p.get("business_type", "UNKNOWN")
            if bt == "B2B":
                stats["b2b"] += 1
            elif bt == "B2C":
                stats["b2c"] += 1
            else:
                stats["unknown"] += 1

            if p.get("stripe_verified"):
                stats["verified"] += 1

        return stats

    async def get_recent(self, limit: int = 10) -> list[dict]:
        """Get most recently scraped products."""
        result = self.db.table(self.TABLE_NAME).select("*").order(
            "scraped_at", desc=True
        ).limit(limit).execute()
        return result.data if result.data else []
