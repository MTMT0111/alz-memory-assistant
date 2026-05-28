"""Caregiving support services for reminders, events, and caregiver links."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime
from typing import Any

from app.database import get_connection
from app.models.caregiver_link import CaregiverLink
from app.models.event_log import EventLog
from app.models.reminder import Reminder

REMINDER_TYPES = {
    "medication",
    "meal",
    "phone_call",
    "sleep",
    "custom",
    "medicine",
    "water",
    "routine",
    "activity",
    "later",
}
REMINDER_STATUS = {"pending", "reminded", "confirmed", "missed", "skipped"}
REMINDER_CONFIRMED_BY = {"patient", "caregiver", "system", "unknown"}
EVENT_TYPES = {
    "agitation",
    "medication_refusal",
    "nighttime",
    "wandering_risk",
    "sleep",
    "repeated_question",
    "other",
}
SEVERITY_LEVELS = {"low", "medium", "high"}


def _now_text() -> str:
    """Return a compact timestamp for care records."""
    return datetime.now().isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    """Normalize loose form values into trimmed text."""
    return str(value or "").strip()


def _normalize_choice(value: Any, allowed: set[str], fallback: str) -> str:
    """Keep choice values predictable for storage and UI rendering."""
    text = _clean_text(value)
    return text if text in allowed else fallback


def _normalize_reminder_type(value: Any) -> str:
    """Keep reminder types compatible with older data while preferring new values."""
    normalized = _clean_text(value).lower()
    aliases = {
        "medicine": "medication",
        "water": "custom",
        "routine": "custom",
        "activity": "custom",
        "later": "custom",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in {"medication", "meal", "phone_call", "sleep", "custom"} else "custom"


def _normalize_status(value: Any) -> str:
    return _normalize_choice(value, REMINDER_STATUS, "pending")


def _normalize_confirmed_by(value: Any) -> str:
    return _normalize_choice(value, REMINDER_CONFIRMED_BY, "unknown")


def list_reminders(profile_id: int, limit: int = 50) -> list[Reminder]:
    """Return recent reminders for one profile."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
                SELECT * FROM reminders
                WHERE user_profile_id = ?
                ORDER BY is_enabled DESC,
                         CASE WHEN scheduled_time IS NULL OR TRIM(scheduled_time) = '' THEN 1 ELSE 0 END ASC,
                         scheduled_time ASC,
                         updated_at DESC,
                         id DESC
                LIMIT ?
                """,
                (profile_id, max(1, min(limit, 100))),
            ).fetchall()

    return [Reminder.from_row(row) for row in rows]


def get_reminder(profile_id: int, reminder_id: int) -> Reminder | None:
    """Return one reminder task for a profile."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT * FROM reminders
            WHERE id = ? AND user_profile_id = ?
            """,
            (reminder_id, profile_id),
        ).fetchone()
    return Reminder.from_row(row) if row else None


def save_reminder(profile_id: int, payload: dict[str, Any]) -> Reminder:
    """Create or update a reminder."""
    now = _now_text()
    reminder_id = payload.get("id")
    reminder_type = _normalize_reminder_type(payload.get("reminder_type"))
    status = _normalize_status(payload.get("status"))
    confirmed_by = _normalize_confirmed_by(payload.get("confirmed_by"))
    confirmed_at = _clean_text(payload.get("confirmed_at"))
    if status == "confirmed" and not confirmed_at:
        confirmed_at = now
    if status != "confirmed":
        confirmed_by = confirmed_by if status in {"missed", "skipped"} else "unknown"
        confirmed_at = confirmed_at if status in {"missed", "skipped"} else ""
    normalized = {
        "reminder_type": reminder_type,
        "title": _clean_text(payload.get("title")) or _default_reminder_title(reminder_type),
        "scheduled_time": _clean_text(payload.get("scheduled_time")),
        "description": _clean_text(payload.get("description")),
        "status": status,
        "confirmed_by": confirmed_by,
        "confirmed_at": confirmed_at,
        "repeat_rule": _clean_text(payload.get("repeat_rule")) or "daily",
        "is_enabled": 1 if payload.get("is_enabled", True) else 0,
        "created_by": _clean_text(payload.get("created_by")) or "family",
        "updated_at": now,
    }

    with closing(get_connection()) as connection:
        if reminder_id:
            existing = connection.execute(
                "SELECT id FROM reminders WHERE id = ? AND user_profile_id = ?",
                (reminder_id, profile_id),
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE reminders
                    SET reminder_type = ?,
                        title = ?,
                        scheduled_time = ?,
                        description = ?,
                        status = ?,
                        confirmed_by = ?,
                        confirmed_at = ?,
                        repeat_rule = ?,
                        is_enabled = ?,
                        created_by = ?,
                        updated_at = ?
                    WHERE id = ? AND user_profile_id = ?
                    """,
                    (
                        normalized["reminder_type"],
                        normalized["title"],
                        normalized["scheduled_time"],
                        normalized["description"],
                        normalized["status"],
                        normalized["confirmed_by"],
                        normalized["confirmed_at"],
                        normalized["repeat_rule"],
                        normalized["is_enabled"],
                        normalized["created_by"],
                        normalized["updated_at"],
                        reminder_id,
                        profile_id,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM reminders WHERE id = ?",
                    (reminder_id,),
                ).fetchone()
                return Reminder.from_row(row)

        connection.execute(
            """
            INSERT INTO reminders (
                user_profile_id, reminder_type, title, scheduled_time,
                description, status, confirmed_by, confirmed_at,
                repeat_rule, is_enabled, created_by, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                normalized["reminder_type"],
                normalized["title"],
                normalized["scheduled_time"],
                normalized["description"],
                normalized["status"],
                normalized["confirmed_by"],
                normalized["confirmed_at"],
                normalized["repeat_rule"],
                normalized["is_enabled"],
                normalized["created_by"],
                now,
                now,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM reminders WHERE id = last_insert_rowid()"
        ).fetchone()

    return Reminder.from_row(row)


def toggle_reminder(profile_id: int, reminder_id: int, enabled: bool) -> Reminder | None:
    """Toggle a reminder without changing its schedule."""
    now = _now_text()
    with closing(get_connection()) as connection:
        connection.execute(
            """
            UPDATE reminders
            SET is_enabled = ?, updated_at = ?
            WHERE id = ? AND user_profile_id = ?
            """,
            (1 if enabled else 0, now, reminder_id, profile_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM reminders WHERE id = ? AND user_profile_id = ?",
            (reminder_id, profile_id),
        ).fetchone()

    return Reminder.from_row(row) if row else None


def update_reminder_status(
    profile_id: int,
    reminder_id: int,
    *,
    status: str,
    confirmed_by: str = "unknown",
) -> Reminder | None:
    """Update one reminder task status in a predictable way."""
    now = _now_text()
    normalized_status = _normalize_status(status)
    normalized_confirmed_by = _normalize_confirmed_by(confirmed_by)
    confirmed_at = now if normalized_status == "confirmed" else ""
    with closing(get_connection()) as connection:
        connection.execute(
            """
            UPDATE reminders
            SET status = ?,
                confirmed_by = ?,
                confirmed_at = ?,
                updated_at = ?
            WHERE id = ? AND user_profile_id = ?
            """,
            (
                normalized_status,
                normalized_confirmed_by if normalized_status == "confirmed" else "unknown",
                confirmed_at,
                now,
                reminder_id,
                profile_id,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM reminders WHERE id = ? AND user_profile_id = ?",
            (reminder_id, profile_id),
        ).fetchone()
    return Reminder.from_row(row) if row else None


def confirm_reminder(profile_id: int, reminder_id: int, confirmed_by: str = "caregiver") -> Reminder | None:
    """Mark one reminder as confirmed."""
    return update_reminder_status(
        profile_id,
        reminder_id,
        status="confirmed",
        confirmed_by=confirmed_by,
    )


def mark_reminder_missed(profile_id: int, reminder_id: int) -> Reminder | None:
    """Mark one reminder as missed."""
    return update_reminder_status(
        profile_id,
        reminder_id,
        status="missed",
        confirmed_by="system",
    )


def skip_reminder(profile_id: int, reminder_id: int) -> Reminder | None:
    """Mark one reminder as skipped."""
    return update_reminder_status(
        profile_id,
        reminder_id,
        status="skipped",
        confirmed_by="caregiver",
    )


def build_reminder_status_summary(reminders: list[Reminder]) -> dict[str, Any]:
    """Return caregiver-facing counts for the current reminder list."""
    counts = {
        "confirmed": 0,
        "pending": 0,
        "missed": 0,
        "skipped": 0,
        "reminded": 0,
    }
    for reminder in reminders:
        if not reminder.is_enabled:
            continue
        counts[reminder.status] = counts.get(reminder.status, 0) + 1
    return {
        **counts,
        "enabled_total": sum(counts.values()),
    }


def get_medication_reminder_status(profile_id: int) -> dict[str, Any]:
    """Return the most relevant medication reminder for patient-facing medication questions."""
    reminders = [
        reminder for reminder in list_reminders(profile_id, limit=20)
        if reminder.is_enabled and reminder.reminder_type == "medication"
    ]
    if not reminders:
        return {
            "has_medication_reminder": False,
            "status": "unknown",
            "title": "",
            "scheduled_time": "",
            "description": "",
        }
    reminder = sorted(reminders, key=lambda item: (item.scheduled_time or "99:99", item.id or 0))[0]
    return {
        "has_medication_reminder": True,
        "id": reminder.id,
        "status": reminder.status or "pending",
        "title": reminder.title,
        "scheduled_time": reminder.scheduled_time,
        "description": reminder.description,
        "confirmed_by": reminder.confirmed_by,
        "confirmed_at": reminder.confirmed_at,
    }


def build_daily_care_overview(
    *,
    patient_id: str,
    reminders: list[Reminder],
    caregiver_events: list[Any],
) -> dict[str, Any]:
    """Build one caregiver-facing daily care loop summary."""
    reminder_summary = build_reminder_status_summary(reminders)
    risk_summary = {
        "high": 0,
        "medium": 0,
        "low": 0,
        "unresolved": 0,
    }
    for event in caregiver_events:
        severity = getattr(event, "severity", None) or str(getattr(event, "severity", "") or "low")
        if severity in {"high", "medium", "low"}:
            risk_summary[severity] = risk_summary.get(severity, 0) + 1
        if not bool(getattr(event, "resolved", False)):
            risk_summary["unresolved"] += 1

    if risk_summary["high"] > 0 or reminder_summary["missed"] > 0:
        overall_status = "high_risk"
    elif risk_summary["unresolved"] > 0 or reminder_summary["pending"] > 0:
        overall_status = "needs_attention"
    else:
        overall_status = "stable"

    suggested_actions: list[str] = []
    if reminder_summary["missed"] > 0:
        suggested_actions.append("优先确认未完成提醒，尤其是今日用药与晚间安全。")
    if reminder_summary["pending"] > 0:
        suggested_actions.append("联系家属确认待确认提醒，避免让患者自己判断。")
    if risk_summary["unresolved"] > 0:
        suggested_actions.append("处理未关闭的风险事件，并记录家属跟进结果。")
    if not suggested_actions:
        suggested_actions.append("今日整体稳定，可补充熟悉素材或安排一次安抚通话。")

    return {
        "patient_id": patient_id,
        "date": datetime.now().date().isoformat(),
        "overall_status": overall_status,
        "reminder_summary": {
            "total": reminder_summary["enabled_total"],
            "confirmed": reminder_summary["confirmed"],
            "pending": reminder_summary["pending"],
            "missed": reminder_summary["missed"],
            "skipped": reminder_summary["skipped"],
        },
        "risk_summary": risk_summary,
        "suggested_actions": suggested_actions,
    }


def list_event_logs(profile_id: int, limit: int = 30) -> list[EventLog]:
    """Return recent care event logs for one profile."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT * FROM event_logs
            WHERE user_profile_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (profile_id, max(1, min(limit, 100))),
        ).fetchall()

    return [EventLog.from_row(row) for row in rows]


def create_event_log(profile_id: int, payload: dict[str, Any]) -> EventLog:
    """Record one caregiver-observed event."""
    now = _now_text()
    event_type = _normalize_choice(payload.get("event_type"), EVENT_TYPES, "other")
    severity = _normalize_choice(payload.get("severity"), SEVERITY_LEVELS, "low")

    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO event_logs (
                user_profile_id, event_type, severity, description,
                source, created_by, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                event_type,
                severity,
                _clean_text(payload.get("description")),
                _clean_text(payload.get("source")) or "caregiver",
                _clean_text(payload.get("created_by")) or "family",
                now,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM event_logs WHERE id = last_insert_rowid()"
        ).fetchone()

    return EventLog.from_row(row)


def list_caregiver_links(profile_id: int, limit: int = 20) -> list[CaregiverLink]:
    """Return caregivers linked to one profile."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT * FROM caregiver_links
            WHERE user_profile_id = ?
            ORDER BY is_primary DESC, id DESC
            LIMIT ?
            """,
            (profile_id, max(1, min(limit, 50))),
        ).fetchall()

    return [CaregiverLink.from_row(row) for row in rows]


def create_caregiver_link(profile_id: int, payload: dict[str, Any]) -> CaregiverLink:
    """Create a lightweight caregiver link for future collaboration flows."""
    now = _now_text()
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO caregiver_links (
                user_profile_id, caregiver_name, caregiver_role,
                contact_info, is_primary, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                profile_id,
                _clean_text(payload.get("caregiver_name")) or "家属",
                _clean_text(payload.get("caregiver_role")) or "family",
                _clean_text(payload.get("contact_info")),
                1 if payload.get("is_primary", False) else 0,
                now,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM caregiver_links WHERE id = last_insert_rowid()"
        ).fetchone()

    return CaregiverLink.from_row(row)


def build_care_digest(
    reminders: list[Reminder],
    events: list[EventLog],
    caregivers: list[CaregiverLink],
) -> dict[str, Any]:
    """Build a compact care-oriented digest for templates and APIs."""
    enabled_reminders = [reminder for reminder in reminders if reminder.is_enabled]
    event_type_counts: dict[str, int] = {}
    high_priority_events = []

    for event in events:
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        if event.severity in {"medium", "high"}:
            high_priority_events.append(event)

    return {
        "enabled_reminder_count": len(enabled_reminders),
        "reminder_status_summary": build_reminder_status_summary(reminders),
        "recent_event_count": len(events),
        "primary_caregiver": next((item.to_dict() for item in caregivers if item.is_primary), None),
        "event_type_counts": event_type_counts,
        "high_priority_event_count": len(high_priority_events),
        "latest_event": events[0].to_dict() if events else None,
    }


def _default_reminder_title(reminder_type: str) -> str:
    """Return a readable default title for reminder creation."""
    return {
        "medication": "吃药提醒",
        "meal": "用餐提醒",
        "phone_call": "电话提醒",
        "sleep": "睡前提醒",
        "custom": "照护提醒",
        "medicine": "吃药提醒",
        "water": "喝水提醒",
        "routine": "作息提醒",
        "activity": "活动提醒",
        "later": "稍后提醒一次",
    }.get(reminder_type, "照护提醒")
