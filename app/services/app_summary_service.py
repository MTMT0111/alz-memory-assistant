"""Summary builders for the mobile app shell home screens."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from app.models.chat_log import ChatLog
from app.models.event_log import EventLog
from app.models.reminder import Reminder
from app.models.user_profile import UserProfile
from app.services.location_safety import LocationSafetyService

REMINDER_TYPE_LABELS = {
    "medicine": "吃药",
    "water": "喝水",
    "routine": "休息",
    "activity": "活动",
    "later": "稍后",
}

EVENT_TYPE_LABELS = {
    "agitation": "情绪激越",
    "medication_refusal": "拒药",
    "nighttime": "夜间异常",
    "wandering_risk": "离家倾向",
    "sleep": "睡眠异常",
    "repeated_question": "重复提问增加",
    "other": "其他事件",
}

QUICK_ACTIONS = [
    {"label": "Profile", "href": "/profile-editor"},
    {"label": "Reminders", "href": "/device-settings"},
    {"label": "Care Log", "href": "/memory-notes"},
    {"label": "Safety", "href": "/location-safety"},
    {"label": "Settings", "href": "/device-settings"},
]


def _now_time_text() -> str:
    """Return a compact local time string for patient home."""
    return datetime.now().strftime("%H:%M")


def _voice_ready() -> bool:
    """Use current env config as a simple voice-ready indicator."""
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _sorted_enabled_reminders(reminders: list[Reminder]) -> list[Reminder]:
    """Keep active reminders ordered for next-item summary rendering."""
    enabled = [item for item in reminders if item.is_enabled]
    return sorted(
        enabled,
        key=lambda item: (
            item.scheduled_time or "99:99",
            item.updated_at or "",
            item.id or 0,
        ),
    )


def _build_next_reminder(reminders: list[Reminder]) -> dict[str, Any] | None:
    """Return the next enabled reminder in a UI-friendly shape."""
    enabled = _sorted_enabled_reminders(reminders)
    if not enabled:
        return None

    next_item = enabled[0]
    return {
        "type": next_item.reminder_type,
        "type_label": REMINDER_TYPE_LABELS.get(next_item.reminder_type, "提醒"),
        "time": next_item.scheduled_time or "--:--",
        "title": next_item.title or "今日提醒",
        "repeat_rule": next_item.repeat_rule,
        "created_by": next_item.created_by or "family",
    }


def _build_recent_chat(logs: list[ChatLog]) -> dict[str, Any]:
    """Return the latest visible chat item or a gentle empty state."""
    if not logs:
        return {
            "has_data": False,
            "role": "assistant",
            "message": "还没有新的对话记录，我们可以从一句轻轻的问候开始。",
            "timestamp": "",
        }

    latest = logs[0]
    return {
        "has_data": True,
        "role": latest.role,
        "message": latest.message or "最近有一条对话。",
        "timestamp": latest.timestamp,
    }


def _resolve_location_status(profile: UserProfile) -> dict[str, Any]:
    """Fetch real location status when available, otherwise return a safe empty fallback."""
    service = LocationSafetyService()
    candidate_ids = [str(profile.id)] if profile.id is not None else []
    candidate_ids.append("demo-patient")

    for patient_id in candidate_ids:
        try:
            status = service.get_location_status(patient_id)
        except Exception:  # pragma: no cover - defensive summary fallback
            continue
        latest_location = status.get("latest_location")
        safe_zone = status.get("safe_zone")
        latest_alert = status.get("latest_alert")
        if latest_location or safe_zone or latest_alert:
            return {
                "has_real_data": bool(latest_location or safe_zone or latest_alert),
                "patient_id": patient_id,
                "device_online": bool(latest_location),
                "location_label": latest_location.get("address_text") or "在家附近" if latest_location else "未开启定位",
                "last_reported_at": latest_location.get("timestamp", "") if latest_location else "",
                "inside_safe_zone": status.get("inside_safe_zone"),
                "safe_zone_missing": status.get("safe_zone_missing", True),
                "has_wandering_risk": bool(latest_alert),
                "summary": status.get("caregiver_summary") or "暂未获取到定位状态。",
            }

    return {
        "has_real_data": False,
        "patient_id": "demo-patient",
        "device_online": False,
        "location_label": "未开启定位",
        "last_reported_at": "",
        "inside_safe_zone": None,
        "safe_zone_missing": True,
        "has_wandering_risk": False,
        "summary": "定位安全还没有启用，后续接入设备后会显示最近上报和安全区域状态。",
    }


def build_patient_summary(
    *,
    profile: UserProfile,
    reminders: list[Reminder],
    recent_logs: list[ChatLog],
) -> dict[str, Any]:
    """Build the focused patient-side app home summary."""
    location_status = _resolve_location_status(profile)
    next_reminder = _build_next_reminder(reminders)
    return {
        "current_status": {
            "label": "陪伴中",
            "voice_status": "语音可用" if _voice_ready() else "语音未配置",
            "voice_ready": _voice_ready(),
            "current_time": _now_time_text(),
        },
        "next_reminder": next_reminder,
        "recent_chat": _build_recent_chat(recent_logs),
        "safety_status": {
            "label": "在家" if location_status["device_online"] and location_status["inside_safe_zone"] is not False else location_status["location_label"],
            "device_online": location_status["device_online"],
            "last_reported_at": location_status["last_reported_at"],
            "summary": location_status["summary"],
        },
    }


def build_caregiver_summary(
    *,
    profile: UserProfile,
    reminders: list[Reminder],
    events: list[EventLog],
    recent_logs: list[ChatLog],
    memory_digest: dict[str, object],
) -> dict[str, Any]:
    """Build the caregiver-side app dashboard summary."""
    next_reminder = _build_next_reminder(reminders)
    enabled_count = sum(1 for item in reminders if item.is_enabled)
    closed_count = sum(1 for item in reminders if not item.is_enabled)
    pending_count = enabled_count
    completed_count = 0
    latest_log_time = recent_logs[0].timestamp if recent_logs else ""
    location_status = _resolve_location_status(profile)
    wandering_events = [item for item in events if item.event_type == "wandering_risk"]

    recent_events = [
        {
            "event_type": item.event_type,
            "event_type_label": EVENT_TYPE_LABELS.get(item.event_type, "其他事件"),
            "severity": item.severity,
            "description": item.description or "已记录一条照护事件。",
            "created_at": item.created_at,
        }
        for item in events[:4]
    ]

    return {
        "reminder_summary": {
            "total_count": len(reminders),
            "completed_count": completed_count,
            "pending_count": pending_count,
            "closed_count": closed_count,
            "next_reminder": next_reminder,
        },
        "recent_events": recent_events,
        "memory_summary": {
            "mentioned_people": memory_digest.get("mentioned_people", []),
            "follow_up_topics": memory_digest.get("follow_up_topics", []),
            "summary": memory_digest.get("summary") or "最近还没有足够的对话摘要。",
            "last_updated_at": latest_log_time,
        },
        "safety_summary": {
            "device_online": location_status["device_online"],
            "recent_location": location_status["location_label"],
            "safe_zone_status": (
                "安全区域内"
                if location_status["inside_safe_zone"] is True
                else "离开安全区域"
                if location_status["inside_safe_zone"] is False
                else "未开启定位"
            ),
            "has_wandering_risk_event": bool(wandering_events or location_status["has_wandering_risk"]),
            "summary": location_status["summary"],
        },
        "quick_actions": QUICK_ACTIONS,
    }
