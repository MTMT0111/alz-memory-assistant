#!/usr/bin/env python3
"""Initialize demo patient profile in the database."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.demo_data import demo_patient
from app.database import get_connection
from app.init_db import initialize_database
from app.services import care_service, familiar_material_service, profile_service


def _find_existing_demo_profile_id() -> int | None:
    """Return the existing 李桂兰 demo profile id, if present."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM user_profiles WHERE name IN (?, ?) ORDER BY updated_at DESC, id DESC LIMIT 1",
            (demo_patient.PATIENT_NAME, demo_patient.PATIENT_NICKNAME),
        ).fetchone()
    return int(row["id"]) if row else None


def _seed_reminders(profile_id: int) -> int:
    """Create missing demo reminders without duplicating existing title/time pairs."""
    existing = {
        (reminder.title, reminder.scheduled_time)
        for reminder in care_service.list_reminders(profile_id)
    }
    created = 0
    for reminder in demo_patient.get_demo_reminders():
        key = (reminder["title"], reminder["time"])
        if key in existing:
            continue
        reminder_type = "custom"
        title = reminder["title"]
        if "药" in title:
            reminder_type = "medication"
        elif "饭" in title:
            reminder_type = "meal"
        elif "电话" in title:
            reminder_type = "phone_call"
        elif "睡" in title:
            reminder_type = "sleep"
        care_service.save_reminder(
            profile_id,
            {
                "reminder_type": reminder_type,
                "title": title,
                "scheduled_time": reminder["time"],
                "description": reminder.get("description", ""),
                "status": "pending",
                "confirmed_by": "unknown",
                "repeat_rule": "daily",
                "is_enabled": True,
                "created_by": "demo_seed",
            },
        )
        created += 1
    return created


def _seed_caregivers(profile_id: int) -> int:
    """Create missing caregiver links for the demo family."""
    existing_names = {
        caregiver.caregiver_name
        for caregiver in care_service.list_caregiver_links(profile_id)
    }
    caregivers = demo_patient.get_demo_caregivers()
    payloads = [
        {
            "caregiver_name": caregivers["primary"]["name"],
            "caregiver_role": caregivers["primary"]["relationship"],
            "contact_info": caregivers["primary"]["contact"],
            "is_primary": True,
        },
        {
            "caregiver_name": caregivers["secondary"]["name"],
            "caregiver_role": caregivers["secondary"]["relationship"],
            "contact_info": caregivers["secondary"]["status"],
            "is_primary": False,
        },
    ]

    created = 0
    for payload in payloads:
        if payload["caregiver_name"] in existing_names:
            continue
        care_service.create_caregiver_link(profile_id, payload)
        created += 1
    return created


def seed_demo_patient():
    """Create or update demo patient profile."""
    # Initialize database
    initialize_database()

    # Create demo patient profile
    demo_data = demo_patient.get_demo_patient_profile()
    existing_id = _find_existing_demo_profile_id()
    if existing_id:
        demo_data["id"] = existing_id
    profile = profile_service.save_profile(demo_data)
    reminder_count = _seed_reminders(profile.id or 0)
    caregiver_count = _seed_caregivers(profile.id or 0)
    material_count = familiar_material_service.seed_demo_materials(profile.id or 0)

    print(f"✓ Demo patient profile created/updated:")
    print(f"  Patient ID: {profile.id}")
    print(f"  Name: {profile.name}")
    print(f"  Age: {profile.age}")
    print(f"  Hometown: {profile.hometown}")
    print(f"  Support Mode: {profile.support_mode}")
    print(f"  Reminders added: {reminder_count}")
    print(f"  Caregivers added: {caregiver_count}")
    print(f"  Familiar materials added: {material_count}")

    return profile


if __name__ == "__main__":
    try:
        profile = seed_demo_patient()
        print("\n✓ Demo patient ready for testing!")
        print(f"\nRun dialogue test with:")
        print(f"  python scripts/test_deepseek_demo_patient.py --provider deepseek")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
