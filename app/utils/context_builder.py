"""Prompt context builders that expose the generic companion memory layers."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.chat_log import ChatLog
from app.models.user_profile import UserProfile
from app.services.memory_context_service import (
    build_long_term_memory_summary,
    build_profile_memory,
    build_session_memory,
)


def build_system_prompt_context(system_prompt: str) -> str:
    """Wrap the single Alzheimer prompt in a labeled section."""
    prompt_text = system_prompt.strip() or "当前未提供额外系统提示。"
    return "\n".join(["【系统提示】", prompt_text])


def build_profile_context(profile: UserProfile) -> str:
    """Expose static profile memory as a clean prompt block."""
    return build_profile_memory(profile).text


def build_recent_history_context(chat_logs: Sequence[ChatLog]) -> str:
    """Expose short-term session memory from the latest turns."""
    session_memory = build_session_memory(chat_logs)
    return "\n".join(["【session_memory】", session_memory.text])


def build_current_message_context(user_message: str) -> str:
    """Wrap the latest user message in a labeled section."""
    return "\n".join(["【当前用户消息】", user_message.strip() or "（空消息）"])


def build_memory_summary_context(memory_summary: str) -> str:
    """Expose distilled long-term memory as a separate labeled section."""
    summary_text = build_long_term_memory_summary(memory_summary).text
    return "\n".join(["【long_term_memory_summary】", summary_text])


def build_full_context(
    *,
    system_prompt: str,
    profile: UserProfile,
    chat_logs: Sequence[ChatLog],
    user_message: str,
    memory_summary: str = "",
) -> str:
    """Combine the three memory layers plus current input for debugging and tracing."""
    return "\n\n".join(
        [
            build_system_prompt_context(system_prompt),
            "【profile_memory】",
            build_profile_context(profile),
            build_memory_summary_context(memory_summary),
            build_recent_history_context(chat_logs),
            build_current_message_context(user_message),
        ]
    )
