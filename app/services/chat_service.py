"""Conversation orchestration for the Alzheimer companion and memory assistant."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from app.config import SUPPORT_MODE, SUPPORT_MODE_DESCRIPTION, SUPPORT_MODE_LABEL
from app.database import get_connection
from app.models.chat_log import ChatLog
from app.services import analysis_service, care_service, caregiver_event_service, conversation_style_engine, diagnostics_service, familiar_material_service, memory_candidate_service, profile_service
from app.services.llm_service import LLMConversationInput, LLMReplyResult, get_llm_runtime_status, get_llm_service
from app.services.memory_context_service import build_long_term_memory_summary, build_profile_memory, build_session_memory
from app.utils.context_builder import build_full_context

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "alzheimer_prompt.txt"
LAST_CHAT_DIAGNOSTICS: dict[str, Any] = {}


def _now_text() -> str:
    """Return a compact local timestamp for chat logs."""
    return datetime.now().isoformat(timespec="seconds")


def _load_prompt() -> str:
    """Read the Alzheimer companion prompt from disk."""
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def get_support_meta() -> dict[str, str]:
    """Return the single fixed support-scene metadata for the UI."""
    return {
        "value": SUPPORT_MODE,
        "label": SUPPORT_MODE_LABEL,
        "description": SUPPORT_MODE_DESCRIPTION,
    }


def _caregiver_patient_id(profile) -> str:
    """Return a stable caregiver-event patient key for current app flows."""
    if getattr(profile, "name", "") in {"李奶奶", "李桂兰"}:
        return "demo_patient_001"
    return f"profile_{profile.id or 0}"


def get_recent_chat_logs(
    user_id: int | None,
    limit: int = 10,
    mode: str | None = None,
) -> list[ChatLog]:
    """Fetch recent conversation history in chronological order."""
    if user_id is None:
        return []

    normalized_mode = SUPPORT_MODE if mode else None

    with closing(get_connection()) as connection:
        if normalized_mode:
            rows = connection.execute(
                """
                SELECT * FROM chat_logs
                WHERE user_id = ? AND mode = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, normalized_mode, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM chat_logs
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

    # Query newest-first for efficiency, then reverse so prompts and UI read naturally.
    return [ChatLog.from_row(row) for row in reversed(rows)]


def _insert_chat_log(
    connection,
    *,
    user_id: int,
    role: str,
    message: str,
    mode: str,
    keyword_tags: str,
    repeated_flag: bool,
) -> ChatLog:
    """Persist one chat message and return the stored row as a model."""
    timestamp = _now_text()
    cursor = connection.execute(
        """
        INSERT INTO chat_logs (user_id, role, message, timestamp, mode, keyword_tags, repeated_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, role, message, timestamp, mode, keyword_tags, int(repeated_flag)),
    )
    row = connection.execute(
        "SELECT * FROM chat_logs WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return ChatLog.from_row(row)


def _memory_usage_snapshot(profile, recent_logs: list[ChatLog], memory_summary: str) -> dict[str, Any]:
    """Return a privacy-safe summary of which memory layers were available to chat."""
    profile_memory = build_profile_memory(profile)
    session_memory = build_session_memory(recent_logs)
    long_term_memory = build_long_term_memory_summary(memory_summary)

    def _section(lines: list[str], label: str) -> dict[str, Any]:
        return {
            "used": bool(lines),
            "line_count": len(lines),
            "labels": [label] if lines else [],
        }

    profile_section = _section(profile_memory.lines, "profile_memory")
    session_section = _section(session_memory.lines, "session_memory")
    long_term_section = _section(long_term_memory.lines, "long_term_memory_summary")

    return {
        "memory_context_used": any(
            section["used"]
            for section in (profile_section, session_section, long_term_section)
        ),
        "profile_memory_used": profile_section,
        "session_memory_used": session_section,
        "long_term_memory_used": long_term_section,
    }


def _build_reminder_summary(profile_id: int | None) -> str:
    """Return a compact routine/reminder block for the LLM context."""
    if profile_id is None:
        return ""
    reminders = care_service.list_reminders(profile_id)
    enabled = [reminder for reminder in reminders if reminder.is_enabled]
    if not enabled:
        return "今日提醒：暂无已启用提醒。"
    lines = []
    for reminder in enabled[:6]:
        time_text = reminder.scheduled_time or "未设时间"
        status_text = {
            "confirmed": "已确认",
            "missed": "未确认",
            "skipped": "已跳过",
            "reminded": "已提醒",
        }.get(reminder.status, "待确认")
        lines.append(f"{time_text} {reminder.title}（{status_text}）")
    return "今日作息/提醒：" + "；".join(lines)


def _build_risk_rule_summary(style_state) -> str:
    """Return only the current care-risk boundary, not all rules."""
    scenario = getattr(style_state, "care_scenario", "general") or "general"
    rules = {
        "repeated_question_xiaoyu": "重复问小雨：耐心复述小雨晚上 8 点左右联系，不说“你问过”。",
        "medication_confusion": "用药不确定：不能判断已吃/没吃，建议看药盒或请小雨确认。",
        "medication_uncertainty": "用药不确定：不能判断已吃/没吃，建议看药盒或请小雨确认。",
        "wandering_risk": "外出风险：不要鼓励独自外出，先安抚并联系家属。",
        "wandering_intent": "外出风险：不要鼓励独自外出，先安抚并联系家属。",
        "going_home": "位置困惑/想回家：不争辩，不强行断言位置，先安抚并确认安全。",
        "disorientation_going_home": "位置困惑/想回家：不争辩，不强行断言位置，先安抚并确认安全。",
        "sensitive_deceased_spouse_topic": "已故亲人敏感话题：不直接说去世，先接住想念，再转向陪伴或老歌。",
        "deceased_spouse_sensitive": "已故亲人敏感话题：不直接说去世，先接住想念，再转向陪伴或老歌。",
    }
    return rules.get(scenario, "当前规则：保持短句、温和、不责备；复杂决定交给家属一起确认。")


def _build_medication_reply(profile_id: int | None) -> tuple[str, dict[str, Any]] | None:
    """Return a deterministic medication reply from reminder status, never from LLM guesswork."""
    if profile_id is None:
        return None
    reminder_status = care_service.get_medication_reminder_status(profile_id)
    status = str(reminder_status.get("status") or "unknown")
    if status == "confirmed":
        return (
            "李奶奶，今天早上的药已经确认过了。我们先安心坐一会儿。",
            reminder_status,
        )
    if status == "missed":
        return (
            "我这里看到今天的药还没有确认。先别自己乱吃，我们请小雨确认一下。",
            reminder_status,
        )
    return (
        "我这里还没有看到确认记录。我们一起请小雨确认一下，好吗？",
        reminder_status,
    )


def _count_context_items(*sections: str) -> int:
    """Count non-empty compact context lines for diagnostics."""
    count = 0
    for section in sections:
        for line in str(section or "").splitlines():
            if line.strip():
                count += 1
    return count


def build_conversation_context(
    *,
    profile,
    recent_logs: list[ChatLog],
    memory_summary: str,
    familiar_material_summary: str,
    reminder_summary: str,
    risk_rule_summary: str,
) -> str:
    """Build a compact chat context: recent 4 turns raw, older content summarized."""
    earlier_logs = recent_logs[:-4]
    earlier_summary = ""
    if earlier_logs:
        earlier_digest = analysis_service.build_memory_digest(profile, earlier_logs)
        earlier_summary = str(earlier_digest.get("summary") or "")
    sections = [
        memory_summary,
        earlier_summary and f"更早对话压缩摘要：{earlier_summary}",
        reminder_summary,
        risk_rule_summary,
        familiar_material_summary and "熟悉素材摘要（仅在合适时使用，敏感素材不主动提）：\n" + familiar_material_summary,
    ]
    return "\n".join(section for section in sections if section)


def build_chat_diagnostics(
    *,
    llm_result: LLMReplyResult,
    recent_logs_with_user: list[ChatLog],
    profile,
    memory_summary: str,
    chat_latency_ms: int,
    user_message: str,
    style_state,
    context_items_count: int = 0,
    materials_used: list[dict[str, Any]] | None = None,
    material_match_reason: str = "",
    history_turns_used: int = 0,
    reminder_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a frontend-safe diagnostics block without exposing prompt contents."""
    memory_usage = _memory_usage_snapshot(profile, recent_logs_with_user, memory_summary)
    diagnosis = diagnostics_service.build_chat_diagnosis(
        requested_provider=llm_result.requested_provider,
        actual_provider=llm_result.actual_provider,
        fallback_used=llm_result.fallback_used,
        fallback_reason=llm_result.fallback_reason,
        guard_triggered=llm_result.guard_triggered,
        guard_reason=llm_result.guard_reason,
        memory_context_used=memory_usage["memory_context_used"],
        profile_memory_used=memory_usage["profile_memory_used"],
        session_memory_used=memory_usage["session_memory_used"],
        long_term_memory_used=memory_usage["long_term_memory_used"],
        user_message=user_message,
        style_state=style_state,
    )
    detected_state = getattr(style_state, "care_scenario", "general") or "general"
    strategy = conversation_style_engine.decide_strategy(style_state) if style_state else "normal_chat"
    runtime_status = get_llm_runtime_status(llm_result.requested_provider)
    return {
        "provider": llm_result.actual_provider,
        "requested_provider": llm_result.requested_provider,
        "actual_provider": llm_result.actual_provider,
        "model": llm_result.model,
        "requested_model": runtime_status.get("model") or llm_result.model,
        "base_url": runtime_status.get("base_url") or "",
        "api_key_configured": bool(runtime_status.get("api_key_configured")),
        "fallback_enabled": bool(runtime_status.get("fallback_enabled")),
        "fallback_used": llm_result.fallback_used,
        "fallback_reason": llm_result.fallback_reason or None,
        "postprocess_used": llm_result.postprocess_used,
        "template_used": llm_result.template_used,
        "template_name": llm_result.template_name or None,
        "safe_template_reply": llm_result.safe_template_reply or None,
        "guard_triggered": llm_result.guard_triggered,
        "guard_reason": llm_result.guard_reason or None,
        "raw_llm_reply": llm_result.raw_llm_reply or None,
        "final_assistant_reply": llm_result.reply,
        "detected_state": detected_state,
        "strategy": strategy,
        "response_time_ms": chat_latency_ms,
        "memory_context_used": memory_usage["memory_context_used"],
        "memory_used": memory_usage["memory_context_used"],
        "context_items_count": context_items_count,
        "materials_used": materials_used or [],
        "material_match_reason": material_match_reason,
        "history_turns_used": history_turns_used,
        "reminder_status": reminder_status or {},
        "profile_memory_used": memory_usage["profile_memory_used"],
        "session_memory_used": memory_usage["session_memory_used"],
        "long_term_memory_used": memory_usage["long_term_memory_used"],
        "chat_latency_ms": chat_latency_ms,
        "diagnosis": diagnosis.to_dict(),
    }


def generate_chat_reply(
    user_id: int | None,
    message: str,
    mode: str | None = None,
) -> dict[str, Any]:
    """Generate a reply, store both sides of the conversation, and return the payload."""
    clean_message = message.strip()
    if not clean_message:
        raise ValueError("message cannot be empty")

    profile = profile_service.get_profile_by_id(user_id) if user_id else None
    if profile is None:
        profile = profile_service.ensure_default_profile()

    active_mode = SUPPORT_MODE
    recent_logs = get_recent_chat_logs(profile.id, limit=10, mode=active_mode)
    last_reply = conversation_style_engine.get_last_assistant_reply(recent_logs)
    style_state = conversation_style_engine.detect_user_state(clean_message, recent_logs)
    prompt_text = _load_prompt()
    user_analysis = analysis_service.analyze_user_message(clean_message, recent_logs)

    with closing(get_connection()) as connection:
        user_log = _insert_chat_log(
            connection,
            user_id=profile.id or 0,
            role="user",
            message=clean_message,
            mode=active_mode,
            keyword_tags=str(user_analysis["keyword_tags"]),
            repeated_flag=bool(user_analysis["repeated_flag"]),
        )
        connection.commit()

    memory_candidate = memory_candidate_service.capture_candidate_from_message(
        profile.id or 0,
        clean_message,
    )

    recent_logs_with_user = [*recent_logs, user_log][-10:]
    memory_digest = analysis_service.build_memory_digest(profile, recent_logs_with_user)
    memory_summary = str(memory_digest["summary"])
    reminder_summary = _build_reminder_summary(profile.id)
    risk_rule_summary = _build_risk_rule_summary(style_state)
    material_matches = familiar_material_service.match_materials(
        profile.id or 0,
        clean_message,
    )
    familiar_material_summary = familiar_material_service.build_prompt_summary(
        profile.id or 0,
        clean_message,
    )
    prompt_memory_summary = build_conversation_context(
        profile=profile,
        recent_logs=recent_logs_with_user,
        memory_summary=memory_summary,
        familiar_material_summary=familiar_material_summary,
        reminder_summary=reminder_summary,
        risk_rule_summary=risk_rule_summary,
    )
    context_items_count = _count_context_items(
        prompt_memory_summary,
        reminder_summary,
        risk_rule_summary,
        familiar_material_summary,
    )
    material_match_items = [match.to_dict() for match in material_matches if match.matched_terms or match.material.is_sensitive]
    material_match_reason = "；".join(
        f"{item['title']}：{item['reason']}"
        for item in material_match_items[:4]
    )
    reminder_status = care_service.get_medication_reminder_status(profile.id or 0)
    context_text = build_full_context(
        system_prompt=prompt_text,
        profile=profile,
        chat_logs=recent_logs,
        user_message=clean_message,
        memory_summary=prompt_memory_summary,
    )
    conversation = LLMConversationInput(
        system_prompt=prompt_text,
        support_mode=active_mode,
        profile=profile,
        recent_logs=recent_logs,
        user_message=clean_message,
        context_text=context_text,
        memory_summary=prompt_memory_summary,
        last_reply=last_reply,
        style_state=style_state,
        style_strategy=conversation_style_engine.decide_strategy(style_state),
    )
    forced_medication_reply = (
        _build_medication_reply(profile.id)
        if getattr(style_state, "care_scenario", "") in {"medication_confusion", "medication_uncertainty"}
        else None
    )
    if forced_medication_reply:
        reply, reminder_status = forced_medication_reply
        runtime_status = get_llm_runtime_status("deepseek")
        llm_result = LLMReplyResult(
            reply=reply,
            requested_provider="deepseek",
            actual_provider="template_fallback",
            model=str(runtime_status.get("model") or "deepseek-v4-flash"),
            fallback_used=True,
            fallback_reason="template_fallback: medication_status_guard",
            guard_triggered=True,
            guard_reason="medication_status_guard",
            raw_llm_reply="",
            postprocess_used=True,
            safe_template_reply=reply,
            template_used=True,
            template_name="medication_status_guard",
        )
        chat_latency_ms = 0
    else:
        llm_started_at = perf_counter()
        llm_result = get_llm_service().generate_reply_result(conversation)
        chat_latency_ms = max(0, int(round((perf_counter() - llm_started_at) * 1000)))
        reply = llm_result.reply
    assistant_analysis = analysis_service.analyze_assistant_message(reply)

    with closing(get_connection()) as connection:
        assistant_log = _insert_chat_log(
            connection,
            user_id=profile.id or 0,
            role="assistant",
            message=reply,
            mode=active_mode,
            keyword_tags=str(assistant_analysis["keyword_tags"]),
            repeated_flag=False,
        )
        connection.commit()

    recent_user_messages = [log.message for log in recent_logs if log.role == "user"]
    caregiver_capture = caregiver_event_service.capture_turn_events(
        patient_id=_caregiver_patient_id(profile),
        user_profile_id=profile.id,
        source_message=clean_message,
        assistant_reply=reply,
        recent_user_messages=recent_user_messages,
        source_turn=f"chat_log:{user_log.id or ''}",
    )

    refreshed_profile = profile_service.touch_profile(profile.id) or profile
    updated_logs = get_recent_chat_logs(profile.id, limit=10, mode=active_mode)
    updated_memory_digest = analysis_service.build_memory_digest(refreshed_profile, updated_logs)
    diagnostics = build_chat_diagnostics(
        llm_result=llm_result,
        recent_logs_with_user=recent_logs_with_user,
        profile=profile,
        memory_summary=memory_summary,
        chat_latency_ms=chat_latency_ms,
        user_message=clean_message,
        style_state=style_state,
        context_items_count=context_items_count,
        materials_used=material_match_items,
        material_match_reason=material_match_reason,
        history_turns_used=min(len(recent_logs_with_user), 4),
        reminder_status=reminder_status,
    )
    diagnostics.update(
        {
            "user_message": clean_message,
            "final_assistant_reply": reply,
            "caregiver_events_created": len(caregiver_capture.events),
            "reminder_events_created": 1 if caregiver_capture.reminder_event_created else 0,
            "caregiver_risk_level": caregiver_capture.risk_level,
            "familiar_materials_used": bool(familiar_material_summary),
            "familiar_material_summary": familiar_material_summary,
            "materials_used": material_match_items,
            "material_match_reason": material_match_reason,
            "context_items_count": context_items_count,
            "memory_used": True,
            "history_turns_used": min(len(recent_logs_with_user), 4),
            "reminder_status": reminder_status,
            "created_at": _now_text(),
            "memory_candidate_created": memory_candidate.to_dict() if memory_candidate else None,
        }
    )
    global LAST_CHAT_DIAGNOSTICS
    LAST_CHAT_DIAGNOSTICS = dict(diagnostics)

    return {
        "reply": reply,
        "mode": active_mode,
        "profile": refreshed_profile.to_dict(),
        "logs": [user_log.to_dict(), assistant_log.to_dict()],
        "analysis": user_analysis,
        "mode_meta": get_support_meta(),
        "context_text": context_text,
        "memory_digest": updated_memory_digest,
        "diagnostics": diagnostics,
        "caregiver_events": caregiver_capture.to_dict(),
        "debug": diagnostics,
    }


def get_last_chat_diagnostics() -> dict[str, Any]:
    """Return the most recent in-process chat diagnostics for local debugging."""
    return dict(LAST_CHAT_DIAGNOSTICS)
