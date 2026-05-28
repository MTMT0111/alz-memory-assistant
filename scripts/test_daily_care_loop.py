#!/usr/bin/env python3
"""Smoke test the daily care loop summary and medication confirmation flow."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_local_env_file

load_local_env_file()

from app.main import get_daily_care_today
from app.services import care_service, caregiver_event_service, chat_service, profile_service


def _find_medication_reminder(profile_id: int):
    reminders = care_service.list_reminders(profile_id, limit=20)
    medication = [
        reminder for reminder in reminders
        if reminder.is_enabled and reminder.reminder_type == "medication"
    ]
    if not medication:
        raise RuntimeError("missing demo medication reminder")
    return sorted(medication, key=lambda item: (item.scheduled_time or "99:99", item.id or 0))[0]


def main() -> int:
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    patient_key = "demo_patient_001"
    medication = _find_medication_reminder(profile.id or 0)

    care_service.confirm_reminder(profile.id or 0, medication.id or 0, confirmed_by="caregiver")
    summary_confirmed = asyncio.run(get_daily_care_today(patient_key))
    if int((summary_confirmed.get("reminder_summary") or {}).get("confirmed", 0)) < 1:
        print("FAIL: confirmed reminder did not appear in daily care summary")
        return 1

    confirmed_reply = chat_service.generate_chat_reply(
        user_id=profile.id,
        message="我是不是还没吃药？",
    )["reply"]
    if "已经确认过了" not in confirmed_reply:
        print(f"FAIL: confirmed medication reply mismatch: {confirmed_reply}")
        return 1

    care_service.mark_reminder_missed(profile.id or 0, medication.id or 0)
    summary_missed = asyncio.run(get_daily_care_today(patient_key))
    if (summary_missed.get("overall_status") or "") != "high_risk":
        print(f"FAIL: expected high_risk after missed medication, got {summary_missed.get('overall_status')}")
        return 1
    if int((summary_missed.get("reminder_summary") or {}).get("missed", 0)) < 1:
        print("FAIL: missed reminder did not appear in daily care summary")
        return 1

    missed_reply = chat_service.generate_chat_reply(
        user_id=profile.id,
        message="我是不是还没吃药？",
    )["reply"]
    if "先别自己乱吃" not in missed_reply:
        print(f"FAIL: missed medication reply mismatch: {missed_reply}")
        return 1

    print("PASS: daily care loop reflects reminder status and medication replies.")
    print(f"confirmed summary: {summary_confirmed}")
    print(f"missed summary: {summary_missed}")
    print(f"caregiver events today: {len(caregiver_event_service.list_events(patient_key))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
