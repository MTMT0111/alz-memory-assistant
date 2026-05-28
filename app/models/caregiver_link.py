"""Caregiver link model for lightweight family collaboration structure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CaregiverLink:
    """Represents one caregiver connected to a profile."""

    id: int | None = None
    user_profile_id: int = 0
    caregiver_name: str = ""
    caregiver_role: str = ""
    contact_info: str = ""
    is_primary: bool = False
    created_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "CaregiverLink":
        """Build a caregiver link from a SQLite row."""
        return cls(
            id=row["id"],
            user_profile_id=row["user_profile_id"],
            caregiver_name=row["caregiver_name"] or "",
            caregiver_role=row["caregiver_role"] or "",
            contact_info=row["contact_info"] or "",
            is_primary=bool(row["is_primary"]),
            created_at=row["created_at"] or "",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly caregiver mapping."""
        return {
            "id": self.id,
            "user_profile_id": self.user_profile_id,
            "caregiver_name": self.caregiver_name,
            "caregiver_role": self.caregiver_role,
            "contact_info": self.contact_info,
            "is_primary": self.is_primary,
            "created_at": self.created_at,
        }
