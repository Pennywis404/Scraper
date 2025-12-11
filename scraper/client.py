import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from scraper.models import Product
from scraper.queries import POSTS_TODAY, POSTS_BY_DATE


class ProductHuntClient:
    """Client for Product Hunt GraphQL API."""

    def __init__(self, api_token: str, base_url: str, rate_limit_delay: int = 1):
        self.api_token = api_token
        self.base_url = base_url
        self.rate_limit_delay = rate_limit_delay
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _execute_query(self, query: str, variables: dict) -> dict:
        """Execute a GraphQL query."""
        client = await self._get_client()
        response = await client.post(
            self.base_url,
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data.get("data", {})

    async def get_today_posts(self, limit: int = 50) -> list[Product]:
        """Get today's Product Hunt posts."""
        products = []
        after = None

        while len(products) < limit:
            await asyncio.sleep(self.rate_limit_delay)

            data = await self._execute_query(
                POSTS_TODAY,
                {"first": min(20, limit - len(products)), "after": after},
            )

            posts_data = data.get("posts", {})
            nodes = posts_data.get("nodes", [])

            for node in nodes:
                products.append(Product.from_api_response(node))

            page_info = posts_data.get("pageInfo", {})
            if not page_info.get("hasNextPage") or len(products) >= limit:
                break

            after = page_info.get("endCursor")

        return products[:limit]

    async def get_posts_by_date(
        self,
        date: datetime,
        limit: int = 50
    ) -> list[Product]:
        """Get Product Hunt posts from a specific date."""
        products = []
        after = None

        # Set time range for the date
        posted_after = date.replace(hour=0, minute=0, second=0, microsecond=0)
        posted_before = posted_after + timedelta(days=1)

        while len(products) < limit:
            await asyncio.sleep(self.rate_limit_delay)

            data = await self._execute_query(
                POSTS_BY_DATE,
                {
                    "postedAfter": posted_after.isoformat(),
                    "postedBefore": posted_before.isoformat(),
                    "first": min(20, limit - len(products)),
                    "after": after,
                },
            )

            posts_data = data.get("posts", {})
            nodes = posts_data.get("nodes", [])

            for node in nodes:
                products.append(Product.from_api_response(node))

            page_info = posts_data.get("pageInfo", {})
            if not page_info.get("hasNextPage") or len(products) >= limit:
                break

            after = page_info.get("endCursor")

        return products[:limit]
