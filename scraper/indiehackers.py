# -*- coding: utf-8 -*-
"""
Indie Hackers Products Scraper using Playwright.
Scrapes products from https://www.indiehackers.com/products
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional
from playwright.async_api import async_playwright, Page


@dataclass
class IndieProduct:
    """Represents an Indie Hackers product."""
    name: str
    tagline: str = ""
    revenue: str = ""
    url: str = ""
    website: Optional[str] = None
    categories: list[str] = field(default_factory=list)
    stripe_verified: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tagline": self.tagline,
            "revenue": self.revenue,
            "url": self.url,
            "website": self.website,
            "categories": self.categories,
            "stripe_verified": self.stripe_verified,
        }


class IndieHackersClient:
    """Scraper for Indie Hackers products page."""

    BASE_URL = "https://www.indiehackers.com/products"

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser = None
        self._playwright = None

    async def _init_browser(self):
        """Initialize Playwright browser."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)

    async def close(self):
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None

    async def _scroll_and_load(self, page: Page, target_count: int, max_scrolls: int = 50):
        """Scroll the page to load more products."""
        loaded = 0
        scrolls = 0

        while loaded < target_count and scrolls < max_scrolls:
            # Count current products
            loaded = await page.locator(".product-card").count()

            if loaded >= target_count:
                break

            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)  # Wait for loading

            scrolls += 1

        return loaded

    def _clean_revenue(self, raw: str) -> str:
        """Clean revenue string to extract just the amount."""
        import re
        # Find pattern like $123,456
        match = re.search(r'\$[\d,]+', raw)
        if match:
            return match.group(0) + "/month"
        return raw.strip()

    async def _extract_products(self, page: Page) -> list[IndieProduct]:
        """Extract product data from the page."""
        products = []

        # Get all product cards
        cards = page.locator(".product-card")
        count = await cards.count()

        for i in range(count):
            card = cards.nth(i)

            try:
                # Extract data from each card
                name = await card.locator(".product-card__name").text_content() or ""
                tagline = await card.locator(".product-card__tagline").text_content() or ""

                # Revenue (may not exist for all products)
                revenue_el = card.locator(".product-card__revenue")
                revenue = ""
                stripe_verified = False

                if await revenue_el.count() > 0:
                    raw_revenue = await revenue_el.text_content() or ""
                    revenue = self._clean_revenue(raw_revenue)

                    # Check if Stripe verified (logo present)
                    stripe_logo = card.locator(".product-card__stripe-logo")
                    stripe_verified = await stripe_logo.count() > 0

                # URL
                link = card.locator("a").first
                href = await link.get_attribute("href") or ""
                url = f"https://www.indiehackers.com{href}" if href.startswith("/") else href

                products.append(IndieProduct(
                    name=name.strip(),
                    tagline=tagline.strip(),
                    revenue=revenue,
                    url=url,
                    stripe_verified=stripe_verified,
                ))

            except Exception as e:
                print(f"Error extracting product {i}: {e}")
                continue

        return products

    async def get_products(
        self,
        limit: int = 50,
        sorting: str = "highest-revenue",
        revenue_verification: str = "stripe",
    ) -> list[IndieProduct]:
        """
        Scrape products from Indie Hackers.

        Args:
            limit: Maximum number of products to scrape
            sorting: Sort order (highest-revenue, newest, etc.)
            revenue_verification: Filter by verification (stripe, any, none)

        Returns:
            List of IndieProduct objects
        """
        await self._init_browser()

        page = await self._browser.new_page()

        try:
            # Build URL with filters
            url = f"{self.BASE_URL}?sorting={sorting}"
            if revenue_verification:
                url += f"&revenueVerification={revenue_verification}"

            print(f"🔍 Navigating to: {url}")
            await page.goto(url, timeout=60000)

            # Wait for products to load
            await page.wait_for_selector(".product-card", timeout=30000)
            await page.wait_for_timeout(2000)

            # Scroll to load more products
            print(f"📜 Loading products (target: {limit})...")
            loaded = await self._scroll_and_load(page, limit)
            print(f"✅ Loaded {loaded} products")

            # Extract products
            print("📊 Extracting data...")
            products = await self._extract_products(page)

            return products[:limit]

        finally:
            await page.close()


async def main():
    """Test the scraper."""
    client = IndieHackersClient(headless=True)

    try:
        products = await client.get_products(limit=10)

        print(f"\n{'='*50}")
        print(f"Found {len(products)} products")
        print('='*50)

        for p in products:
            verified = "✅ Stripe" if p.stripe_verified else "❌ Non vérifié"
            print(f"\n{p.name}")
            print(f"  Tagline: {p.tagline[:50]}..." if len(p.tagline) > 50 else f"  Tagline: {p.tagline}")
            print(f"  Revenue: {p.revenue}")
            print(f"  Verified: {verified}")
            print(f"  URL: {p.url}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
