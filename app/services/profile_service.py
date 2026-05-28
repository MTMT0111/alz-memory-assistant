"""CRUD helpers for user profiles persisted in SQLite."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime
from typing import Any

from app.database import get_connection
from app.config import SUPPORT_MODE
from app.memory_data import build_default_profile_payload
from app.models.user_profile import UserProfile


def _now_text() -> str:
    """Return a compact local timestamp for storage."""
    return datetime.now().isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    """Convert loose form values into trimmed text."""
    return str(value or "").strip()


def _clean_age(value: Any) -> int | None:
    """Convert age input to an integer when possible."""
    if value in (None, ""):
        return None

    try:
        age = int(value)
    except (TypeError, ValueError):
        return None

    return age if age >= 0 else None


def get_default_profile_payload() -> dict[str, Any]:
    """Expose the seeded profile so initialization and fallbacks stay in sync."""
    return build_default_profile_payload()


def get_blank_profile() -> UserProfile:
    """Return a profile-shaped object for template rendering before persistence."""
    defaults = get_default_profile_payload()
    return UserProfile(
        id=None,
        name=str(defaults["name"]),
        age=int(defaults["age"]),
        hometown=str(defaults["hometown"]),
        support_mode=str(defaults["support_mode"]),
        family_info=str(defaults["family_info"]),
        life_events=str(defaults["life_events"]),
        preferences=str(defaults["preferences"]),
        notes=str(defaults["notes"]),
        created_at="",
        updated_at="",
    )


def get_profile_by_id(profile_id: int | None) -> UserProfile | None:
    """Look up a profile by primary key."""
    if profile_id is None:
        return None

    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM user_profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()

    return UserProfile.from_row(row) if row else None


def get_latest_profile() -> UserProfile | None:
    """Return the most recently updated profile, if one exists."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM user_profiles ORDER BY updated_at DESC, id DESC LIMIT 1"
        ).fetchone()

    return UserProfile.from_row(row) if row else None


def save_profile(payload: dict[str, Any]) -> UserProfile:
    """Insert or update a profile using form data from the frontend."""
    now = _now_text()
    profile_id = payload.get("id")

    normalized = {
        "name": _clean_text(payload.get("name")) or "陪伴对象",
        "age": _clean_age(payload.get("age")),
        "hometown": _clean_text(payload.get("hometown")),
        "support_mode": SUPPORT_MODE,
        "family_info": _clean_text(payload.get("family_info")),
        "life_events": _clean_text(payload.get("life_events")),
        "preferences": _clean_text(payload.get("preferences")),
        "notes": _clean_text(payload.get("notes")),
        "updated_at": now,
    }

    with closing(get_connection()) as connection:
        if profile_id is not None:
            existing = connection.execute(
                "SELECT created_at FROM user_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE user_profiles
                    SET name = ?,
                        age = ?,
                        hometown = ?,
                        support_mode = ?,
                        family_info = ?,
                        life_events = ?,
                        preferences = ?,
                        notes = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        normalized["name"],
                        normalized["age"],
                        normalized["hometown"],
                        normalized["support_mode"],
                        normalized["family_info"],
                        normalized["life_events"],
                        normalized["preferences"],
                        normalized["notes"],
                        normalized["updated_at"],
                        profile_id,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM user_profiles WHERE id = ?",
                    (profile_id,),
                ).fetchone()
                return UserProfile.from_row(row)

        connection.execute(
            """
            INSERT INTO user_profiles (
                name, age, hometown, support_mode, family_info, life_events,
                preferences, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized["name"],
                normalized["age"],
                normalized["hometown"],
                normalized["support_mode"],
                normalized["family_info"],
                normalized["life_events"],
                normalized["preferences"],
                normalized["notes"],
                now,
                now,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM user_profiles WHERE id = last_insert_rowid()"
        ).fetchone()

    return UserProfile.from_row(row)


def ensure_default_profile() -> UserProfile:
    """Guarantee that at least one profile exists for the demo experience."""
    existing = get_latest_profile()
    if existing is not None:
        return existing

    return save_profile(get_default_profile_payload())


def touch_profile(profile_id: int | None) -> UserProfile | None:
    """Refresh a profile's updated timestamp so the active conversation remains current."""
    if profile_id is None:
        return None

    now = _now_text()
    with closing(get_connection()) as connection:
        connection.execute(
            "UPDATE user_profiles SET updated_at = ? WHERE id = ?",
            (now, profile_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM user_profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()

    return UserProfile.from_row(row) if row else None
