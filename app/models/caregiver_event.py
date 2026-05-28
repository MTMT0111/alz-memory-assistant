"""Caregiver insight event model for rule-triggered care feedback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CaregiverEvent:
    """Represents one rule-triggered caregiver-facing event."""

    id: str = ""
    patient_id: str = ""
    user_profile_id: int | None = None
    event_type: str = "safety_check"
    severity: str = "low"
    title: str = ""
    description: str = ""
    source_message: str = ""
    source_turn: str = ""
    assistant_reply: str = ""
    suggested_action: str = ""
    tags: str = ""
    created_at: str = ""
    resolved: bool = False

    @classmethod
    def from_row(cls, row: Any) -> "CaregiverEvent":
        """Build a caregiver event from a SQLite row."""
        return cls(
            id=row["id"] or "",
            patient_id=row["patient_id"] or "",
            user_profile_id=row["user_profile_id"],
            event_type=row["event_type"] or "safety_check",
            severity=row["severity"] or "low",
            title=row["title"] or "",
            description=row["description"] or "",
            source_message=row["source_message"] or "",
            source_turn=row["source_turn"] or "",
            assistant_reply=row["assistant_reply"] or "",
            suggested_action=row["suggested_action"] or "",
            tags=row["tags"] or "",
            created_at=row["created_at"] or "",
            resolved=bool(row["resolved"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly mapping."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "user_profile_id": self.user_profile_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "source_message": self.source_message,
            "source_turn": self.source_turn,
            "assistant_reply": self.assistant_reply,
            "suggested_action": self.suggested_action,
            "tags": [tag.strip() for tag in self.tags.split(",") if tag.strip()],
            "created_at": self.created_at,
            "resolved": self.resolved,
        }
