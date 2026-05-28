"""Structured memory-layer builders for the generic companion framework.

This module keeps the three memory layers explicit:
1. profile_memory: static profile details entered by family or users
2. session_memory: short-term conversational context from recent turns
3. long_term_memory_summary: compact distilled observations from longer usage

The LLM layer should receive these layers as separate support blocks instead of
one mixed transcript.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Sequence

from app.models.chat_log import ChatLog
from app.models.user_profile import UserProfile


@dataclass(slots=True)
class ProfileMemory:
    """Static profile memory entered through the product UI."""

    lines: list[str]

    @property
    def text(self) -> str:
        """Return the profile block as a multi-line string."""
        return "\n".join(self.lines) if self.lines else "暂无资料。"


@dataclass(slots=True)
class SessionMemory:
    """Short-term conversational memory from the latest turns."""

    lines: list[str]
    last_assistant_reply: str

    @property
    def text(self) -> str:
        """Return the recent context block as a multi-line string."""
        return "\n".join(self.lines) if self.lines else "暂无最近对话。"


@dataclass(slots=True)
class LongTermMemorySummary:
    """Compact long-term memory distilled from repeated usage."""

    lines: list[str]

    @property
    def text(self) -> str:
        """Return the long-term summary block as a multi-line string."""
        return "\n".join(self.lines) if self.lines else "暂无稳定的长期摘要。"


def build_profile_memory(profile: UserProfile) -> ProfileMemory:
    """Turn UI-entered profile fields into short factual lines for the model."""
    lines: list[str] = []

    base_parts: list[str] = []
    if profile.name:
        base_parts.append(f"姓名：{profile.name}")
    if profile.age is not None:
        base_parts.append(f"年龄：约{profile.age}岁")
    if profile.hometown:
        base_parts.append(f"熟悉城市：{profile.hometown}")
    if base_parts:
        lines.append("；".join(base_parts))

    if profile.family_info:
        lines.append(f"重要家人：{profile.family_info}")
    if profile.life_events:
        lines.append(f"过去经历：{profile.life_events}")
    if profile.preferences:
        lines.append(f"喜好：{profile.preferences}")
    if profile.notes:
        lines.append(f"陪伴提醒：{profile.notes}")

    return ProfileMemory(lines=lines[:5])


def build_session_memory(
    chat_logs: Sequence[ChatLog],
    *,
    last_assistant_reply: str = "",
    max_turns: int = 4,
) -> SessionMemory:
    """Keep only a few recent turns as short-term session memory."""
    lines: list[str] = []
    recent_logs = list(chat_logs[-max_turns:])

    for log in recent_logs:
        message = str(log.message or "").strip()
        if not message:
            continue
        role_text = "用户" if log.role == "user" else "助手"
        lines.append(f"{role_text}：{message}")

    normalized_last_reply = last_assistant_reply.strip()
    if not normalized_last_reply:
        for log in reversed(chat_logs):
            if log.role == "assistant" and log.message.strip():
                normalized_last_reply = log.message.strip()
                break

    return SessionMemory(
        lines=lines,
        last_assistant_reply=normalized_last_reply,
    )


def build_long_term_memory_summary(summary_text: str, *, max_lines: int = 4) -> LongTermMemorySummary:
    """Condense long-term summary text into a few short factual lines."""
    raw_lines = [
        line.strip(" -")
        for line in re.split(r"[。\n]", str(summary_text or ""))
        if line.strip(" -")
    ]

    lines: list[str] = []
    for line in raw_lines:
        cleaned = re.sub(r"\s+", " ", line).strip()
        if not cleaned:
            continue
        lines.append(f"- {cleaned[:42]}")
        if len(lines) >= max_lines:
            break

    return LongTermMemorySummary(lines=lines)
