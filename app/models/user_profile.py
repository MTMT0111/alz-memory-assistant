"""User profile model stored in SQLite and reused by the UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class UserProfile:
    """Represents a persisted companion profile."""

    id: int | None = None
    name: str = ""
    age: int | None = None
    hometown: str = ""
    support_mode: str = "alzheimer"
    family_info: str = ""
    life_events: str = ""
    preferences: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "UserProfile":
        """Build a profile object from a SQLite row."""
        return cls(
            id=row["id"],
            name=row["name"] or "",
            age=row["age"],
            hometown=row["hometown"] or "",
            support_mode=row["support_mode"] or "alzheimer",
            family_info=row["family_info"] or "",
            life_events=row["life_events"] or "",
            preferences=row["preferences"] or "",
            notes=row["notes"] or "",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly mapping for templates and API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "hometown": self.hometown,
            "support_mode": self.support_mode,
            "family_info": self.family_info,
            "life_events": self.life_events,
            "preferences": self.preferences,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
