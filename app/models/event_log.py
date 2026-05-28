"""Care event log model for lightweight abnormal-event recording."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EventLog:
    """Represents one caregiver-recorded care event."""

    id: int | None = None
    user_profile_id: int = 0
    event_type: str = "other"
    severity: str = "low"
    description: str = ""
    source: str = "caregiver"
    created_by: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "EventLog":
        """Build an event log from a SQLite row."""
        return cls(
            id=row["id"],
            user_profile_id=row["user_profile_id"],
            event_type=row["event_type"] or "other",
            severity=row["severity"] or "low",
            description=row["description"] or "",
            source=row["source"] or "caregiver",
            created_by=row["created_by"] or "",
            created_at=row["created_at"] or "",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly event mapping."""
        return {
            "id": self.id,
            "user_profile_id": self.user_profile_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "description": self.description,
            "source": self.source,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }
