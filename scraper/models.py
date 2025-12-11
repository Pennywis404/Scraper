from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class BusinessType(Enum):
    B2B = "B2B"
    B2C = "B2C"
    UNKNOWN = "UNKNOWN"


@dataclass
class Product:
    """Represents a Product Hunt launch."""
    id: str
    name: str
    tagline: str
    description: str
    url: str
    website: Optional[str] = None
    votes_count: int = 0
    comments_count: int = 0
    created_at: Optional[datetime] = None
    featured_at: Optional[datetime] = None
    topics: list[str] = field(default_factory=list)

    # Maker info
    maker_name: Optional[str] = None
    maker_twitter: Optional[str] = None

    # Classification fields (filled by AI agent)
    business_type: BusinessType = BusinessType.UNKNOWN
    classification_reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,  # PK = Product Hunt ID
            "name": self.name,
            "tagline": self.tagline,
            "description": self.description,
            "url": self.url,
            "website": self.website,
            "votes_count": self.votes_count,
            "comments_count": self.comments_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "featured_at": self.featured_at.isoformat() if self.featured_at else None,
            "topics": self.topics,
            "maker_name": self.maker_name,
            "maker_twitter": self.maker_twitter,
            "business_type": self.business_type.value,
            "classification_reason": self.classification_reason,
        }

    @classmethod
    def from_api_response(cls, data: dict) -> "Product":
        """Create Product from Product Hunt API response."""
        # Extract first maker info (makers is now a direct list)
        makers = data.get("makers", [])
        maker = makers[0] if makers else {}

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            tagline=data.get("tagline", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            website=data.get("website"),
            votes_count=data.get("votesCount", 0),
            comments_count=data.get("commentsCount", 0),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
                       if data.get("createdAt") else None,
            featured_at=datetime.fromisoformat(data["featuredAt"].replace("Z", "+00:00"))
                        if data.get("featuredAt") else None,
            topics=[t["name"] for t in data.get("topics", {}).get("nodes", [])],
            maker_name=maker.get("name"),
            maker_twitter=maker.get("username"),  # Changed from twitterUsername to username
        )
