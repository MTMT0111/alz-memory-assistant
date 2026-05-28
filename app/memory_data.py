"""Generic seed data so the app boots with editable sample content, not a fixed role."""

from __future__ import annotations


DEFAULT_COMPANION_PROFILE = {
    "name": "陪伴对象",
    "age": None,
    "hometown": "",
    "support_mode": "alzheimer",
    "family_info": "",
    "life_events": "",
    "preferences": "",
    "notes": "可填写更适合的称呼、重要家人、熟悉经历和陪伴提醒。",
}


def build_default_profile_payload() -> dict[str, object]:
    """Return a copy of the default seeded profile so callers can modify it safely."""
    return DEFAULT_COMPANION_PROFILE.copy()
