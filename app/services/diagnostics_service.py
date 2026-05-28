"""Stable diagnostics taxonomy for chat and voice turn debugging."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


Severity = Literal["info", "warning", "error"]


PROVIDER_OK = "provider_ok"
PROVIDER_UNAVAILABLE = "provider_unavailable"
PROVIDER_API_KEY_MISSING = "provider_api_key_missing"
PROVIDER_TIMEOUT = "provider_timeout"
PROVIDER_REQUEST_FAILED = "provider_request_failed"
PROVIDER_FALLBACK_TO_MOCK = "provider_fallback_to_mock"

GUARD_NOT_TRIGGERED = "guard_not_triggered"
RESPONSE_GUARD_TRIGGERED = "response_guard_triggered"
SYSTEM_LIKE_RESPONSE_GUARD = "system_like_response_guard"
FIELD_LEAKAGE_GUARD = "field_leakage_guard"
SCRIPTED_GUIDANCE_GUARD = "scripted_guidance_guard"
UNSAFE_RESPONSE_GUARD = "unsafe_response_guard"
IRRELEVANT_RESPONSE_GUARD = "irrelevant_response_guard"

MEMORY_CONTEXT_USED = "memory_context_used"
MEMORY_CONTEXT_MISSING = "memory_context_missing"
PROFILE_MEMORY_USED = "profile_memory_used"
PROFILE_MEMORY_MISSING = "profile_memory_missing"
SESSION_MEMORY_USED = "session_memory_used"
LONG_TERM_MEMORY_USED = "long_term_memory_used"
MEMORY_TOO_SPARSE = "memory_too_sparse"

VOICE_OK = "voice_ok"
ASR_FAILED = "asr_failed"
TTS_FAILED = "tts_failed"
AUDIO_EMPTY = "audio_empty"
UNSUPPORTED_AUDIO_FORMAT = "unsupported_audio_format"
VOICE_API_KEY_MISSING = "voice_api_key_missing"

NORMAL_CONVERSATION = "normal_conversation"
REMINDER_RELATED = "reminder_related"
MEMORY_QUESTION = "memory_question"
CLARIFICATION = "clarification"
SAFETY_RISK = "safety_risk"
WANDERING_RISK = "wandering_risk"
MEDICATION_RELATED = "medication_related"
CAREGIVER_SUPPORT_NEEDED = "caregiver_support_needed"
MEDICATION_CONFUSION = "medication_confusion"
FEAR_ANXIETY = "fear_anxiety"
GOING_HOME = "going_home"
PERSON_RECOGNITION = "person_recognition"
SUSPICION_OR_DELUSION = "suspicion_or_delusion"


@dataclass(slots=True)
class DiagnosisResult:
    """Human-readable diagnosis plus stable machine tags."""

    tags: list[str]
    primary_issue: str | None
    severity: Severity
    human_summary: str
    suggested_next_step: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dict."""
        return asdict(self)


def _unique_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


def _used_flag(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(value.get("used"))
    return bool(value)


def _line_count(value: Any) -> int:
    if isinstance(value, dict):
        return int(value.get("line_count") or 0)
    return 0


def _fallback_reason_tags(fallback_reason: str) -> list[str]:
    normalized = str(fallback_reason or "").strip().lower()
    tags: list[str] = []
    if not normalized:
        return tags
    if "guard rejected" in normalized:
        return tags
    if "api key missing" in normalized:
        tags.extend([PROVIDER_API_KEY_MISSING, PROVIDER_UNAVAILABLE])
    elif "timeout" in normalized or "timed out" in normalized:
        tags.extend([PROVIDER_TIMEOUT, PROVIDER_UNAVAILABLE])
    elif "client unavailable" in normalized:
        tags.append(PROVIDER_UNAVAILABLE)
    else:
        tags.append(PROVIDER_REQUEST_FAILED)
    return tags


def _guard_reason_tags(guard_reason: str) -> list[str]:
    normalized = str(guard_reason or "").strip().lower()
    tags = [RESPONSE_GUARD_TRIGGERED]
    if not normalized:
        return tags
    if SYSTEM_LIKE_RESPONSE_GUARD in normalized or "system" in normalized or "meta" in normalized:
        tags.append(SYSTEM_LIKE_RESPONSE_GUARD)
    elif FIELD_LEAKAGE_GUARD in normalized or "field" in normalized:
        tags.append(FIELD_LEAKAGE_GUARD)
    elif SCRIPTED_GUIDANCE_GUARD in normalized or "script" in normalized:
        tags.append(SCRIPTED_GUIDANCE_GUARD)
    elif UNSAFE_RESPONSE_GUARD in normalized or "unsafe" in normalized:
        tags.append(UNSAFE_RESPONSE_GUARD)
    elif IRRELEVANT_RESPONSE_GUARD in normalized or "relevance" in normalized or "direct question" in normalized:
        tags.append(IRRELEVANT_RESPONSE_GUARD)
    return tags


def _care_scenario_tags(*, user_message: str, style_state: Any | None = None) -> list[str]:
    tags: list[str] = []
    message = str(user_message or "")
    normalized = message.lower()

    if style_state is not None:
        care_scenario = getattr(style_state, "care_scenario", "general")
        if care_scenario and care_scenario != "general":
            tags.append(str(care_scenario))
        if getattr(style_state, "memory_question", False):
            tags.append(MEMORY_QUESTION)
        if getattr(style_state, "clarification_request", False):
            tags.append(CLARIFICATION)
        if getattr(style_state, "confusion", False) or getattr(style_state, "current_need", None) == "discomfort":
            tags.append(SAFETY_RISK)

    if any(token in message for token in ("药", "吃药", "药盒")):
        tags.extend([MEDICATION_RELATED, MEDICATION_CONFUSION])
    if any(token in message for token in ("提醒", "安排", "几点", "什么时候")):
        tags.append(REMINDER_RELATED)
    if any(token in message for token in ("出门", "走走", "回家")):
        tags.extend([SAFETY_RISK, WANDERING_RISK])
    if any(token in message for token in ("害怕", "不安心", "怕")):
        tags.append(FEAR_ANXIETY)
    if any(token in message for token in ("这里是哪里", "我要回家", "我在哪")):
        tags.append(GOING_HOME)
    if any(token in message for token in ("这个人是谁", "那个人是谁", "这是谁")):
        tags.append(PERSON_RECOGNITION)
    if any(token in message for token in ("偷", "被偷", "拿走", "不见了", "谁拿了")):
        tags.append(SUSPICION_OR_DELUSION)
    if any(token in normalized for token in ("家属", "caregiver")) or any(token in message for token in ("老人", "设备", "联系家人")):
        tags.append(CAREGIVER_SUPPORT_NEEDED)

    if not tags:
        tags.append(NORMAL_CONVERSATION)
    return tags


def build_chat_diagnosis(
    *,
    requested_provider: str,
    actual_provider: str,
    fallback_used: bool,
    fallback_reason: str,
    guard_triggered: bool,
    guard_reason: str,
    memory_context_used: bool,
    profile_memory_used: Any,
    session_memory_used: Any,
    long_term_memory_used: Any,
    user_message: str,
    style_state: Any | None = None,
) -> DiagnosisResult:
    """Build a structured diagnosis for one chat turn."""
    tags: list[str] = []

    if fallback_used and actual_provider == "mock":
        tags.append(PROVIDER_FALLBACK_TO_MOCK)
        tags.extend(_fallback_reason_tags(fallback_reason))
    elif actual_provider:
        tags.append(PROVIDER_OK)

    if guard_triggered:
        tags.extend(_guard_reason_tags(guard_reason or fallback_reason))
    else:
        tags.append(GUARD_NOT_TRIGGERED)

    if memory_context_used:
        tags.append(MEMORY_CONTEXT_USED)
    else:
        tags.append(MEMORY_CONTEXT_MISSING)

    if _used_flag(profile_memory_used):
        tags.append(PROFILE_MEMORY_USED)
    else:
        tags.append(PROFILE_MEMORY_MISSING)

    if _used_flag(session_memory_used):
        tags.append(SESSION_MEMORY_USED)
    if _used_flag(long_term_memory_used):
        tags.append(LONG_TERM_MEMORY_USED)

    total_memory_lines = (
        _line_count(profile_memory_used)
        + _line_count(session_memory_used)
        + _line_count(long_term_memory_used)
    )
    if total_memory_lines <= 2:
        tags.append(MEMORY_TOO_SPARSE)

    tags.extend(_care_scenario_tags(user_message=user_message, style_state=style_state))
    tags = _unique_tags(tags)

    primary_issue: str | None = None
    severity: Severity = "info"
    human_summary = "The turn completed normally with the requested chat path."
    suggested_next_step = "Continue testing more care scenarios and compare provider behavior."

    if RESPONSE_GUARD_TRIGGERED in tags:
        primary_issue = "response_guard"
        severity = "warning"
        if FIELD_LEAKAGE_GUARD in tags:
            human_summary = "The model reply looked like internal structured memory rather than natural conversation."
            suggested_next_step = "Clean memory formatting or strengthen patient-side response instructions."
        elif SYSTEM_LIKE_RESPONSE_GUARD in tags:
            human_summary = "The model reply looked like system or process language rather than patient-facing speech."
            suggested_next_step = "Tighten companion-style instructions and suppress system-like wording."
        elif SCRIPTED_GUIDANCE_GUARD in tags:
            human_summary = "The model reply sounded like a scripted guidance card instead of natural conversation."
            suggested_next_step = "Reduce scripted phrasing and keep the patient-facing reply shorter and more direct."
        elif IRRELEVANT_RESPONSE_GUARD in tags:
            human_summary = "The model reply drifted away from the user’s current question or care need."
            suggested_next_step = "Strengthen current-turn priority and simplify the available memory context."
        elif UNSAFE_RESPONSE_GUARD in tags:
            human_summary = "The model reply looked unsafe or overstimulating for the current care scenario."
            suggested_next_step = "Add a stricter safety rule and expand scenario-specific eval coverage."
        else:
            human_summary = "A response guard rejected the real-model output before it reached the user."
            suggested_next_step = "Review the rejected output pattern and refine the prompt or guard rules."
    elif PROVIDER_API_KEY_MISSING in tags:
        primary_issue = PROVIDER_UNAVAILABLE
        severity = "warning"
        human_summary = "The requested provider was unavailable, so the system used mock fallback."
        suggested_next_step = "Configure the provider API key or switch LLM_PROVIDER to mock for local testing."
    elif PROVIDER_TIMEOUT in tags:
        primary_issue = PROVIDER_TIMEOUT
        severity = "warning"
        human_summary = "The provider request timed out, so the system fell back instead of blocking chat."
        suggested_next_step = "Retry the provider call, inspect network latency, or lower request complexity."
    elif PROVIDER_REQUEST_FAILED in tags or PROVIDER_UNAVAILABLE in tags:
        primary_issue = PROVIDER_UNAVAILABLE
        severity = "warning"
        human_summary = "The requested provider could not complete the turn, so fallback handling was used."
        suggested_next_step = "Inspect provider configuration and upstream request errors."
    elif MEMORY_CONTEXT_MISSING in tags:
        primary_issue = MEMORY_CONTEXT_MISSING
        severity = "info"
        human_summary = "The turn had little or no memory context available to support personalization."
        suggested_next_step = "Add more caregiver-entered profile memory or allow more session history to accumulate."
    elif MEMORY_TOO_SPARSE in tags:
        primary_issue = MEMORY_TOO_SPARSE
        severity = "info"
        human_summary = "The available memory context was present but still sparse for strong personalization."
        suggested_next_step = "Add a few more profile details or longer interaction history for richer memory support."
    elif WANDERING_RISK in tags or SAFETY_RISK in tags or MEDICATION_RELATED in tags:
        primary_issue = "care_scenario_attention"
        severity = "warning"
        human_summary = "The turn touched a care-sensitive scenario that should stay short, calm, and safety-oriented."
        suggested_next_step = "Review whether the reply redirects to family help and avoids complex patient-side decisions."

    return DiagnosisResult(
        tags=tags,
        primary_issue=primary_issue,
        severity=severity,
        human_summary=human_summary,
        suggested_next_step=suggested_next_step,
    )


def build_voice_diagnosis(
    *,
    stage: str,
    success: bool,
    error_code: str | None = None,
) -> DiagnosisResult:
    """Build a structured diagnosis for one voice stage."""
    tags: list[str] = []
    primary_issue: str | None = None
    severity: Severity = "info"
    human_summary = "The voice stage completed normally."
    suggested_next_step = "Continue testing end-to-end voice turns."

    normalized_error = str(error_code or "").strip().upper()

    if success:
        tags.extend([VOICE_OK, PROVIDER_OK])
    elif normalized_error == "VOICE_API_KEY_MISSING":
        tags.extend([VOICE_API_KEY_MISSING, PROVIDER_API_KEY_MISSING, PROVIDER_UNAVAILABLE])
        primary_issue = PROVIDER_UNAVAILABLE
        severity = "error"
        human_summary = "The voice stage could not run because the audio provider key is missing."
        suggested_next_step = "Configure OPENAI_API_KEY or continue local testing in text mode."
    elif normalized_error == "VOICE_AUDIO_EMPTY":
        tags.extend([AUDIO_EMPTY, ASR_FAILED])
        primary_issue = "voice_asr_failed"
        severity = "error"
        human_summary = "The recording did not contain usable audio for transcription."
        suggested_next_step = "Retry with a shorter recording and confirm microphone capture is working."
    elif normalized_error == "VOICE_UNSUPPORTED_FORMAT":
        tags.extend([UNSUPPORTED_AUDIO_FORMAT, ASR_FAILED])
        primary_issue = "voice_asr_failed"
        severity = "error"
        human_summary = "The uploaded recording format was not accepted by the current voice pipeline."
        suggested_next_step = "Use a supported browser recording format such as webm, mp4, wav, or m4a."
    elif normalized_error == "VOICE_ASR_FAILED":
        tags.append(ASR_FAILED)
        primary_issue = "voice_asr_failed"
        severity = "error"
        human_summary = "The speech-to-text step did not return a reliable transcript."
        suggested_next_step = "Retry the recording and inspect the ASR provider response and latency."
    elif normalized_error == "VOICE_TTS_FAILED":
        tags.append(TTS_FAILED)
        primary_issue = "voice_tts_failed"
        severity = "warning"
        human_summary = "The text reply was available, but speech generation did not complete."
        suggested_next_step = "Keep the text reply visible and inspect the TTS provider configuration and response."
    elif normalized_error == "VOICE_PROVIDER_TIMEOUT":
        tags.extend([PROVIDER_TIMEOUT, PROVIDER_UNAVAILABLE])
        primary_issue = PROVIDER_TIMEOUT
        severity = "warning"
        human_summary = "The voice provider timed out before the stage could finish."
        suggested_next_step = "Retry the request and inspect upstream latency or network conditions."
    else:
        tags.append(TTS_FAILED if stage == "speak" else ASR_FAILED)
        primary_issue = "voice_tts_failed" if stage == "speak" else "voice_asr_failed"
        severity = "warning" if stage == "speak" else "error"
        human_summary = "The voice stage did not complete cleanly."
        suggested_next_step = "Inspect the stage error code and recent voice diagnostics for the failing step."

    return DiagnosisResult(
        tags=_unique_tags(tags),
        primary_issue=primary_issue,
        severity=severity,
        human_summary=human_summary,
        suggested_next_step=suggested_next_step,
    )
