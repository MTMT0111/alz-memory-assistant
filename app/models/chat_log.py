"""Chat log model used for conversation history and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ChatLog:
    """Represents a single stored chat message."""

    id: int | None = None
    user_id: int = 0
    role: str = "user"
    message: str = ""
    timestamp: str = ""
    mode: str = "alzheimer"
    keyword_tags: str = ""
    repeated_flag: bool = False

    @classmethod
    def from_row(cls, row: Any) -> "ChatLog":
        """Build a chat log object from a SQLite row."""
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            role=row["role"] or "user",
            message=row["message"] or "",
            timestamp=row["timestamp"] or "",
            mode=row["mode"] or "alzheimer",
            keyword_tags=row["keyword_tags"] or "",
            repeated_flag=bool(row["repeated_flag"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly mapping for templates and API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "message": self.message,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "keyword_tags": self.keyword_tags,
            "repeated_flag": self.repeated_flag,
        }
