"""Caregiver-reviewed memory candidate model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MEMORY_CANDIDATE_TYPES = {
    "old_event",
    "family_photo",
    "familiar_music",
    "old_place",
    "voice_message",
    "daily_object",
    "sensitive_memory",
}

MEMORY_CANDIDATE_STATUS = {"pending", "approved", "rejected"}


@dataclass(slots=True)
class MemoryCandidate:
    """One long-term memory candidate pending caregiver review."""

    id: int | None = None
    patient_id: int = 0
    source_message: str = ""
    suggested_title: str = ""
    suggested_description: str = ""
    suggested_material_type: str = "old_event"
    related_person: str = ""
    sensitivity_level: str = ""
    status: str = "pending"
    created_at: str = ""
    reviewed_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "MemoryCandidate":
        """Build a candidate from a SQLite row."""
        return cls(
            id=row["id"],
            patient_id=row["patient_id"],
            source_message=row["source_message"] or "",
            suggested_title=row["suggested_title"] or "",
            suggested_description=row["suggested_description"] or "",
            suggested_material_type=row["suggested_material_type"] or "old_event",
            related_person=row["related_person"] or "",
            sensitivity_level=row["sensitivity_level"] or "",
            status=row["status"] or "pending",
            created_at=row["created_at"] or "",
            reviewed_at=row["reviewed_at"] or "",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly mapping."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "source_message": self.source_message,
            "suggested_title": self.suggested_title,
            "suggested_description": self.suggested_description,
            "suggested_material_type": self.suggested_material_type,
            "related_person": self.related_person,
            "sensitivity_level": self.sensitivity_level,
            "status": self.status,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "is_sensitive": self.suggested_material_type == "sensitive_memory" or self.sensitivity_level in {"medium", "high"},
        }
