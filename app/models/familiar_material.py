"""Familiar material model for family-maintained reminiscence cues."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MATERIAL_TYPES = {
    "family_photo",
    "voice_message",
    "familiar_music",
    "old_place",
    "old_event",
    "daily_object",
    "sensitive_memory",
}


@dataclass(slots=True)
class FamiliarMaterial:
    """One lightweight familiar cue linked to a patient profile."""

    id: int | None = None
    patient_id: int = 0
    material_type: str = "old_event"
    title: str = ""
    description: str = ""
    related_person: str = ""
    file_path: str = ""
    thumbnail_url: str = ""
    transcript_text: str = ""
    artist: str = ""
    use_scene: str = ""
    suggested_use_scene: str = ""
    related_time: str = ""
    sensitivity_level: str = ""
    tags: str = ""
    safety_note: str = ""
    is_sensitive: bool = False
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row: Any) -> "FamiliarMaterial":
        """Build a familiar material from a SQLite row."""
        return cls(
            id=row["id"],
            patient_id=row["patient_id"],
            material_type=row["material_type"] or "old_event",
            title=row["title"] or "",
            description=row["description"] or "",
            related_person=row["related_person"] or "",
            file_path=row["file_path"] or "",
            thumbnail_url=row["thumbnail_url"] if "thumbnail_url" in row.keys() else "",
            transcript_text=row["transcript_text"] if "transcript_text" in row.keys() else "",
            artist=row["artist"] if "artist" in row.keys() else "",
            use_scene=row["use_scene"] if "use_scene" in row.keys() else "",
            suggested_use_scene=row["suggested_use_scene"] if "suggested_use_scene" in row.keys() else "",
            related_time=row["related_time"] if "related_time" in row.keys() else "",
            sensitivity_level=row["sensitivity_level"] if "sensitivity_level" in row.keys() else "",
            tags=row["tags"] or "",
            safety_note=row["safety_note"] or "",
            is_sensitive=bool(row["is_sensitive"]),
            is_active=bool(row["is_active"]) if "is_active" in row.keys() else True,
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly mapping."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "material_type": self.material_type,
            "title": self.title,
            "description": self.description,
            "related_person": self.related_person,
            "file_path": self.file_path,
            "url": self.file_path,
            "thumbnail_url": self.thumbnail_url,
            "image_url": self.thumbnail_url or self.file_path,
            "audio_url": self.file_path,
            "music_url": self.file_path,
            "transcript_text": self.transcript_text,
            "artist": self.artist,
            "use_scene": self.use_scene,
            "suggested_use_scene": self.suggested_use_scene,
            "related_time": self.related_time,
            "sensitivity_level": self.sensitivity_level,
            "tags": self.tags,
            "safety_note": self.safety_note,
            "is_sensitive": self.is_sensitive,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
