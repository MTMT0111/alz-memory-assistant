"""Care reminder model for caregiver-configured routine support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _normalize_reminder_type(value: str) -> str:
    normalized = str(value or "").strip().lower()
    aliases = {
        "medicine": "medication",
        "water": "custom",
        "routine": "custom",
        "activity": "custom",
        "later": "custom",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized or "custom"


@dataclass(slots=True)
class Reminder:
    """Represents one routine reminder for a profile."""

    id: int | None = None
    user_profile_id: int = 0
    reminder_type: str = "medication"
    title: str = ""
    scheduled_time: str = ""
    description: str = ""
    status: str = "pending"
    confirmed_by: str = "unknown"
    confirmed_at: str = ""
    repeat_rule: str = "daily"
    is_enabled: bool = True
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "Reminder":
        """Build a reminder from a SQLite row."""
        keys = set(row.keys())
        return cls(
            id=row["id"],
            user_profile_id=row["user_profile_id"],
            reminder_type=_normalize_reminder_type(row["reminder_type"] or "medication"),
            title=row["title"] or "",
            scheduled_time=row["scheduled_time"] or "",
            description=row["description"] if "description" in keys and row["description"] is not None else "",
            status=row["status"] if "status" in keys and row["status"] else "pending",
            confirmed_by=row["confirmed_by"] if "confirmed_by" in keys and row["confirmed_by"] else "unknown",
            confirmed_at=row["confirmed_at"] if "confirmed_at" in keys and row["confirmed_at"] else "",
            repeat_rule=row["repeat_rule"] or "daily",
            is_enabled=bool(row["is_enabled"]),
            created_by=row["created_by"] or "",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly reminder mapping."""
        return {
            "id": self.id,
            "user_profile_id": self.user_profile_id,
            "reminder_type": self.reminder_type,
            "title": self.title,
            "scheduled_time": self.scheduled_time,
            "description": self.description,
            "status": self.status,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at,
            "repeat_rule": self.repeat_rule,
            "is_enabled": self.is_enabled,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
