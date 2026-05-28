"""Rule-based caregiver feedback loop for patient-side conversations."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Sequence
from uuid import uuid4

from app.database import get_connection
from app.models.caregiver_event import CaregiverEvent

EVENT_TYPES = {
    "repeated_question",
    "medication_uncertainty",
    "anxiety",
    "wandering_intent",
    "disorientation",
    "reminiscence_need",
    "suspicion_or_delusion",
    "safety_check",
    "sensitive_deceased_spouse",
    "sensitive_deceased_spouse_topic",
    "date_time_confusion",
    "person_recognition",
}
SEVERITY_LEVELS = {"low", "medium", "high"}
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}

SUGGESTED_ACTIONS = {
    "repeated_question": "建议女儿小雨补充一段语音留言，并在晚上 8 点前后主动联系。",
    "medication_uncertainty": "建议家属核对今日用药记录、药盒和提醒状态。",
    "disorientation": "建议家属确认患者当前位置并进行安抚。",
    "wandering_intent": "建议家属确认患者位置，尽量陪同外出，夜间避免独自出门。",
    "anxiety": "建议家属进行语音安抚，并查看是否有环境、疼痛或等待家人等诱因。",
    "reminiscence_need": "建议家属补充熟悉人物照片或简短称呼信息。",
    "suspicion_or_delusion": "建议家属先安抚情绪，再陪同核对物品位置，避免直接争辩。",
    "safety_check": "建议家属稍后确认患者当前状态。",
    "sensitive_deceased_spouse": "患者提及已故老伴，建议家属使用温和回忆或转移注意力，避免直接刺激性说'他已经去世'。",
    "sensitive_deceased_spouse_topic": "患者提及已故老伴，建议家属使用温和回忆或转移注意力，避免直接刺激。",
    "date_time_confusion": "建议保持日期、时间和作息提醒，可在房间贴一个大字日历。",
    "person_recognition": "建议家属补充熟悉人物的照片、称呼或简短信息，温和引入而不是考试式追问。",
}

EVENT_TITLES = {
    "repeated_question": "重复询问家人回家时间",
    "medication_uncertainty": "患者不确定是否已服药",
    "anxiety": "患者表达害怕或不安心",
    "wandering_intent": "患者表达外出意图",
    "disorientation": "患者出现位置困惑或想回家表达",
    "reminiscence_need": "患者需要人物识别支持",
    "suspicion_or_delusion": "患者怀疑物品被拿走",
    "safety_check": "需要家属确认状态",
    "sensitive_deceased_spouse": "患者提及已故老伴",
    "sensitive_deceased_spouse_topic": "患者提及已故老伴",
    "date_time_confusion": "患者出现日期时间困惑",
    "person_recognition": "患者出现人物识别困难",
}

EVENT_TAGS = {
    "repeated_question": "repeat,family,unmet_need",
    "medication_uncertainty": "medication,reminder_check,family_confirm",
    "anxiety": "emotion,reassurance,trigger_check",
    "wandering_intent": "wandering,location,safety",
    "disorientation": "orientation,going_home,location",
    "reminiscence_need": "person_recognition,photo,memory",
    "suspicion_or_delusion": "suspicion,anxiety,item_check",
    "safety_check": "safety,follow_up",
    "sensitive_deceased_spouse": "grief,sensitive,deceased",
    "sensitive_deceased_spouse_topic": "grief,sensitive,deceased-spouse",
    "date_time_confusion": "orientation,time,cognitive",
    "person_recognition": "recognition,family,cognitive",
}

EVENT_LABELS = {
    "repeated_question": "重复询问",
    "medication_uncertainty": "用药不确定",
    "anxiety": "不安或害怕",
    "wandering_intent": "外出意图",
    "disorientation": "定向困惑",
    "reminiscence_need": "人物回忆需要",
    "suspicion_or_delusion": "疑似被偷妄想",
    "safety_check": "安全确认",
    "sensitive_deceased_spouse": "已故亲人话题",
    "sensitive_deceased_spouse_topic": "已故亲人话题",
    "date_time_confusion": "日期时间困惑",
    "person_recognition": "人物识别困难",
}

SEVERITY_LABELS = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
}


@dataclass(slots=True)
class EventCaptureResult:
    """Summary of caregiver events created for one dialogue turn."""

    events: list[CaregiverEvent]
    risk_level: str
    reminder_event_created: bool

    @property
    def caregiver_event_created(self) -> bool:
        """Return whether any caregiver event was created."""
        return bool(self.events)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly mapping."""
        return {
            "events": [event.to_dict() for event in self.events],
            "risk_level": self.risk_level,
            "caregiver_event_created": self.caregiver_event_created,
            "reminder_event_created": self.reminder_event_created,
        }


def _now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today_prefix() -> str:
    return datetime.now().date().isoformat()


def _normalize_text(text: str) -> str:
    return "".join(ch for ch in str(text or "").strip().lower() if ch not in " ，。！？、,.!?；;：:\n\t")


def _contains_any(message: str, hints: Sequence[str]) -> bool:
    normalized = _normalize_text(message)
    return any(_normalize_text(hint) in normalized for hint in hints)


def _normalize_choice(value: Any, allowed: set[str], fallback: str) -> str:
    text = str(value or "").strip()
    return text if text in allowed else fallback


def _event_exists_today(patient_id: str, event_type: str) -> bool:
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT id FROM caregiver_events
            WHERE patient_id = ?
              AND event_type = ?
              AND resolved = 0
              AND created_at >= ?
            LIMIT 1
            """,
            (patient_id, event_type, _today_prefix()),
        ).fetchone()
    return row is not None


def _insert_event(
    *,
    patient_id: str,
    user_profile_id: int | None,
    event_type: str,
    severity: str,
    title: str,
    description: str,
    source_message: str,
    source_turn: str,
    assistant_reply: str,
    suggested_action: str,
    tags: str,
) -> CaregiverEvent:
    event_id = f"ce_{uuid4().hex[:12]}"
    created_at = _now_text()
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO caregiver_events (
                id, patient_id, user_profile_id, event_type, severity,
                title, description, source_message, source_turn, assistant_reply,
                suggested_action, tags, created_at, resolved
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                event_id,
                patient_id,
                user_profile_id,
                event_type,
                severity,
                title,
                description,
                source_message,
                source_turn,
                assistant_reply,
                suggested_action,
                tags,
                created_at,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM caregiver_events WHERE id = ?",
            (event_id,),
        ).fetchone()
    return CaregiverEvent.from_row(row)


def list_events(patient_id: str, limit: int = 30, include_resolved: bool = True) -> list[CaregiverEvent]:
    """Return recent caregiver events for one patient."""
    patient_key = str(patient_id or "").strip()
    if not patient_key:
        return []

    where_resolved = "" if include_resolved else "AND resolved = 0"
    with closing(get_connection()) as connection:
        rows = connection.execute(
            f"""
            SELECT * FROM caregiver_events
            WHERE patient_id = ?
            {where_resolved}
            ORDER BY resolved ASC, created_at DESC, id DESC
            LIMIT ?
            """,
            (patient_key, max(1, min(limit, 100))),
        ).fetchall()
    return [CaregiverEvent.from_row(row) for row in rows]


def resolve_event(patient_id: str, event_id: str) -> CaregiverEvent | None:
    """Mark one caregiver event as resolved."""
    with closing(get_connection()) as connection:
        connection.execute(
            """
            UPDATE caregiver_events
            SET resolved = 1
            WHERE patient_id = ? AND id = ?
            """,
            (patient_id, event_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM caregiver_events WHERE patient_id = ? AND id = ?",
            (patient_id, event_id),
        ).fetchone()
    return CaregiverEvent.from_row(row) if row else None


def clear_patient_events(patient_id: str) -> int:
    """Remove stored caregiver events for a demo/test patient and return count."""
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "DELETE FROM caregiver_events WHERE patient_id = ?",
            (patient_id,),
        )
        connection.commit()
    return int(cursor.rowcount or 0)


def _repeated_xiaoyu_count(message: str, recent_user_messages: Sequence[str]) -> int:
    target_hints = ("小雨什么时候回来", "小雨回来")
    messages = [*recent_user_messages, message]
    return sum(1 for item in messages if _contains_any(item, target_hints))


def detect_event_candidates(message: str, recent_user_messages: Sequence[str] | None = None) -> list[dict[str, str]]:
    """Detect caregiver event candidates from one user message using deterministic rules."""
    recent = list(recent_user_messages or [])
    candidates: list[dict[str, str]] = []

    if _repeated_xiaoyu_count(message, recent) >= 2:
        candidates.append({
            "event_type": "repeated_question",
            "severity": "medium",
            "suggested_action": SUGGESTED_ACTIONS["repeated_question"],
            "description": "患者连续询问女儿小雨回家时间，可能存在等待焦虑或需要明确提醒。",
        })

    if _contains_any(message, ("我是不是还没吃药", "没吃药", "药吃过", "吃药了吗", "忘记药")):
        candidates.append({
            "event_type": "medication_uncertainty",
            "severity": "medium",
            "suggested_action": SUGGESTED_ACTIONS["medication_uncertainty"],
            "description": "患者不确定今日是否服药，需要家属核对药盒、提醒记录或照护记录。",
        })

    if _contains_any(message, ("我要回家", "这里是哪里", "这是哪里", "我在哪", "现在在哪", "这不是我家", "这里不是我家")):
        candidates.append({
            "event_type": "disorientation",
            "severity": "high",
            "suggested_action": SUGGESTED_ACTIONS["disorientation"],
            "description": "患者表达想回家或不确定当前位置，需要优先确认环境安全和当前位置。",
        })

    if _contains_any(message, ("我想出去走走", "出去走走", "出门走走", "我要出去", "夜里出去", "晚上出去")):
        severity = "high" if _contains_any(message, ("一个人", "自己", "现在就", "晚上", "夜里", "半夜", "夜间")) else "medium"
        candidates.append({
            "event_type": "wandering_intent",
            "severity": severity,
            "suggested_action": SUGGESTED_ACTIONS["wandering_intent"],
            "description": "患者表达外出意图，需关注是否夜间、是否独自外出以及当前位置。",
        })

    if _contains_any(message, ("我害怕", "有点害怕", "我不安心", "不安心", "怕", "没人管我", "被丢下", "是不是没人管我了", "是不是被丢下了")):
        candidates.append({
            "event_type": "anxiety",
            "severity": "medium",
            "suggested_action": SUGGESTED_ACTIONS["anxiety"],
            "description": "患者表达害怕或不安心，需要先安抚情绪并观察诱因。",
        })

    if _contains_any(message, ("老王怎么还没回来", "我老伴去哪了", "我老伴呢", "老伴去哪了", "老王呢", "他怎么还没回来")):
        candidates.append({
            "event_type": "sensitive_deceased_spouse_topic",
            "severity": "medium",
            "suggested_action": SUGGESTED_ACTIONS["sensitive_deceased_spouse_topic"],
            "description": "患者提及已故老伴，患者端需要先安抚和转移，避免直接刺激性纠正。",
        })

    if _contains_any(message, ("这个人是谁", "那个人是谁", "这是谁")):
        candidates.append({
            "event_type": "person_recognition",
            "severity": "medium",
            "suggested_action": SUGGESTED_ACTIONS["person_recognition"],
            "description": "患者对眼前人物身份不确定，适合由家属补充照片、称呼或简单关系提示。",
        })

    if _contains_any(message, ("今天几号", "今天是几号", "现在几点", "今天几月")):
        candidates.append({
            "event_type": "date_time_confusion",
            "severity": "low",
            "suggested_action": SUGGESTED_ACTIONS["date_time_confusion"],
            "description": "患者出现日期或时间困惑，适合用大字日历、时钟和作息提醒辅助。",
        })

    if _contains_any(message, ("偷", "被偷", "拿走", "不见了", "谁拿了", "东西没了", "钱没了")):
        candidates.append({
            "event_type": "suspicion_or_delusion",
            "severity": "medium",
            "suggested_action": SUGGESTED_ACTIONS["suspicion_or_delusion"],
            "description": "患者怀疑物品被拿走，可能伴随焦虑，需要陪同核对而不是直接否定。",
        })

    return candidates


def capture_turn_events(
    *,
    patient_id: str,
    user_profile_id: int | None = None,
    source_message: str,
    assistant_reply: str,
    recent_user_messages: Sequence[str] | None = None,
    source_turn: str = "",
) -> EventCaptureResult:
    """Create caregiver events for one dialogue turn and return the capture result."""
    patient_key = str(patient_id or "").strip()
    if not patient_key:
        return EventCaptureResult(events=[], risk_level="low", reminder_event_created=False)

    created_events: list[CaregiverEvent] = []
    for candidate in detect_event_candidates(source_message, recent_user_messages):
        event_type = _normalize_choice(candidate.get("event_type"), EVENT_TYPES, "safety_check")
        severity = _normalize_choice(candidate.get("severity"), SEVERITY_LEVELS, "low")
        if event_type == "repeated_question" and _event_exists_today(patient_key, event_type):
            continue
        created_events.append(
            _insert_event(
                patient_id=patient_key,
                user_profile_id=user_profile_id,
                event_type=event_type,
                severity=severity,
                title=candidate.get("title") or EVENT_TITLES[event_type],
                description=candidate.get("description") or EVENT_TITLES[event_type],
                source_message=source_message,
                source_turn=source_turn or "patient_dialogue",
                assistant_reply=assistant_reply,
                suggested_action=candidate.get("suggested_action") or SUGGESTED_ACTIONS[event_type],
                tags=candidate.get("tags") or EVENT_TAGS[event_type],
            )
        )

    highest = max((SEVERITY_RANK.get(event.severity, 1) for event in created_events), default=1)
    risk_level = next((key for key, value in SEVERITY_RANK.items() if value == highest), "low")
    return EventCaptureResult(
        events=created_events,
        risk_level=risk_level,
        reminder_event_created=any(event.event_type == "medication_uncertainty" for event in created_events),
    )


def _top_risk_level(events: Sequence[CaregiverEvent]) -> str:
    highest = max((SEVERITY_RANK.get(event.severity, 1) for event in events if not event.resolved), default=1)
    return next((key for key, value in SEVERITY_RANK.items() if value == highest), "low")


def _unique_actions(events: Sequence[CaregiverEvent], limit: int = 4) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()
    for event in events:
        action = event.suggested_action.strip()
        if not action or action in seen or event.resolved:
            continue
        seen.add(action)
        actions.append(action)
        if len(actions) >= limit:
            break
    return actions


def _count_event(events: Sequence[CaregiverEvent], event_type: str) -> int:
    return sum(1 for event in events if event.event_type == event_type)


def _template_summary(patient_name: str, events: Sequence[CaregiverEvent]) -> str:
    active = [event for event in events if not event.resolved]
    if not active:
        return (
            f"今天{patient_name}暂无新的规则风险事件。建议继续关注晚间联系、用药确认和外出安全。"
        )

    parts: list[str] = []
    repeated = _count_event(active, "repeated_question")
    disorientation = _count_event(active, "disorientation")
    medication = _count_event(active, "medication_uncertainty")
    anxiety = _count_event(active, "anxiety")
    wandering = _count_event(active, "wandering_intent")
    suspicion = _count_event(active, "suspicion_or_delusion")
    spouse = _count_event(active, "sensitive_deceased_spouse") + _count_event(active, "sensitive_deceased_spouse_topic")
    date_time = _count_event(active, "date_time_confusion")
    person = _count_event(active, "person_recognition")

    if repeated:
        parts.append(f"重复询问女儿小雨回家时间 {repeated + 1 if repeated == 1 else repeated} 次")
    if disorientation:
        parts.append(f"出现 {disorientation} 次想回家或位置困惑表达")
    if anxiety:
        parts.append(f"出现 {anxiety} 次不安表达")
    if medication:
        parts.append("询问过是否吃药")
    if wandering:
        parts.append(f"出现 {wandering} 次外出意图")
    if spouse:
        parts.append(f"提到已故老伴 {spouse} 次")
    if person:
        parts.append(f"出现 {person} 次人物识别困难")
    if date_time:
        parts.append(f"出现 {date_time} 次日期时间困惑")
    if suspicion:
        parts.append(f"出现 {suspicion} 次怀疑物品被拿走的表达")

    if not parts:
        parts.append("出现需要家属留意的照护信号")

    actions = _unique_actions(active, limit=2)
    action_text = "建议家属确认晚间电话提醒和今日用药情况。"
    if actions:
        action_text = " ".join(actions)
    return f"今天{patient_name}{'，'.join(parts)}。{action_text}"[:180]


def build_summary(patient_id: str, patient_name: str = "李奶奶", limit: int = 30) -> dict[str, Any]:
    """Build a caregiver-facing summary from deterministic events."""
    events = list_events(patient_id, limit=limit, include_resolved=True)
    active_events = [event for event in events if not event.resolved]
    top_events = active_events[:5]
    return {
        "patient_id": patient_id,
        "today_summary": _template_summary(patient_name, events),
        "risk_level": _top_risk_level(events),
        "top_events": [event.to_dict() for event in top_events],
        "suggested_actions": _unique_actions(events, limit=5),
        "event_count": len(active_events),
        "risk_events_count": sum(1 for event in active_events if event.severity in {"medium", "high"}),
        "reminder_events_count": sum(1 for event in active_events if event.event_type == "medication_uncertainty"),
    }


def demo_summary() -> dict[str, Any]:
    """Return stable demo insight content when no real caregiver events exist yet."""
    return {
        "patient_id": "demo_patient_001",
        "today_summary": "今天李奶奶重复询问女儿小雨回家时间 2 次，询问过是否吃药，出现 1 次想回家的表达，并提到已故老伴。建议家属确认今日用药情况，晚上主动电话安抚，并补充一段熟悉的语音留言。",
        "risk_level": "medium",
        "top_events": [
            {
                "id": "demo_disorientation",
                "patient_id": "demo_patient_001",
                "event_type": "disorientation",
                "severity": "high",
                "title": EVENT_TITLES["disorientation"],
                "description": "患者表达想回家，需要确认当前位置和情绪状态。",
                "source_message": "我要回家",
                "source_turn": "demo",
                "assistant_reply": "",
                "suggested_action": "建议家属确认患者当前位置并进行安抚。",
                "tags": ["orientation", "going_home", "location"],
                "created_at": _now_text(),
                "resolved": False,
            },
            {
                "id": "demo_medication",
                "patient_id": "demo_patient_001",
                "event_type": "medication_uncertainty",
                "severity": "medium",
                "title": EVENT_TITLES["medication_uncertainty"],
                "description": "患者不确定是否服药，需要核对今日用药状态。",
                "source_message": "我是不是还没吃药？",
                "source_turn": "demo",
                "assistant_reply": "",
                "suggested_action": "建议家属确认今日用药状态。",
                "tags": ["medication", "reminder_check", "family_confirm"],
                "created_at": _now_text(),
                "resolved": False,
            },
        ],
        "suggested_actions": [
            "晚上给患者打一通电话。",
            "确认今日药物是否已服用。",
            "补充一段女儿语音留言。",
        ],
        "event_count": 2,
        "risk_events_count": 2,
        "reminder_events_count": 1,
    }


def event_label(event_type: str) -> str:
    """Return a Chinese event label for reports."""
    return EVENT_LABELS.get(event_type, event_type)


def severity_label(severity: str) -> str:
    """Return a Chinese severity label for reports."""
    return SEVERITY_LABELS.get(severity, severity)
