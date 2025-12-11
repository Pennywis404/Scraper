from supabase import create_client, Client
from typing import Optional


class SupabaseClient:
    """Singleton client for Supabase."""

    _instance: Optional["SupabaseClient"] = None
    _client: Optional[Client] = None

    def __new__(cls, url: str = None, key: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, url: str = None, key: str = None):
        if self._client is None and url and key:
            self._client = create_client(url, key)

    @property
    def client(self) -> Client:
        if self._client is None:
            raise RuntimeError("Supabase client not initialized. Call with url and key first.")
        return self._client

    def table(self, name: str):
        """Get a table reference."""
        return self.client.table(name)


# Global instance
_db: Optional[SupabaseClient] = None


def init_database(url: str, key: str) -> SupabaseClient:
    """Initialize the database client."""
    global _db
    _db = SupabaseClient(url, key)
    return _db


def get_database() -> SupabaseClient:
    """Get the database client instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_database first.")
    return _db
