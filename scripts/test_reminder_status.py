#!/usr/bin/env python3
"""Smoke test for reminder status lifecycle and medication-safe replies."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.init_db import initialize_database
from app.services import care_service, chat_service


def _load_seed_demo_patient():
    module_path = PROJECT_ROOT / "scripts" / "seed_demo_patient.py"
    spec = importlib.util.spec_from_file_location("project_seed_demo_patient", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/seed_demo_patient.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.seed_demo_patient


seed_demo_patient = _load_seed_demo_patient()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _find_medication_reminder(profile_id: int) -> dict:
    reminders = [item.to_dict() for item in care_service.list_reminders(profile_id)]
    for reminder in reminders:
        if reminder.get("reminder_type") == "medication" and reminder.get("scheduled_time") == "08:00":
            return reminder
    raise AssertionError("No medication reminder found in seeded data")


def main() -> int:
    print("Reminder status smoke test")
    initialize_database()
    profile = seed_demo_patient()
    medication = _find_medication_reminder(profile.id or 0)
    reminder_id = int(medication["id"])

    pending = care_service.save_reminder(
        profile.id or 0,
        {
            "id": reminder_id,
            "reminder_type": "medication",
            "title": medication["title"],
            "scheduled_time": medication["scheduled_time"],
            "description": medication.get("description", ""),
            "status": "pending",
            "confirmed_by": "unknown",
            "is_enabled": True,
        },
    )
    _assert(pending.status == "pending", "Unable to set pending reminder status")

    pending_reply = chat_service.generate_chat_reply(profile.id, "我是不是还没吃药？")["reply"]
    _assert("没有看到确认记录" in pending_reply, f"Unexpected pending reply: {pending_reply}")

    confirmed = care_service.confirm_reminder(profile.id or 0, reminder_id, confirmed_by="caregiver")
    _assert(confirmed is not None and confirmed.status == "confirmed", "Confirm reminder failed")
    confirmed_reply = chat_service.generate_chat_reply(profile.id, "我是不是还没吃药？")["reply"]
    _assert("已经确认过了" in confirmed_reply, f"Unexpected confirmed reply: {confirmed_reply}")

    missed = care_service.mark_reminder_missed(profile.id or 0, reminder_id)
    _assert(missed is not None and missed.status == "missed", "Mark reminder missed failed")
    missed_reply = chat_service.generate_chat_reply(profile.id, "我是不是还没吃药？")["reply"]
    _assert("先别自己乱吃" in missed_reply, f"Unexpected missed reply: {missed_reply}")

    status_summary = care_service.build_reminder_status_summary(care_service.list_reminders(profile.id or 0))
    _assert(status_summary.get("missed", 0) >= 1, "Reminder status summary did not update")

    print("PASS: reminder status lifecycle and medication-safe chat logic are working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
