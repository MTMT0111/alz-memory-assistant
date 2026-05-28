"""Lightweight message analysis plus compact memory-summary compatibility helpers."""

from __future__ import annotations

import re
from collections.abc import Sequence

from app.models.chat_log import ChatLog
from app.models.user_profile import UserProfile
from app.services import memory_service

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")
STOPWORDS = {
    "我们",
    "你们",
    "你",
    "我",
    "是不是",
    "可以",
    "一下",
    "一个",
    "这个",
    "那个",
    "还有",
    "什么",
    "怎么",
    "今天",
    "现在",
    "就是",
    "然后",
    "真的",
}


def normalize_message_text(message: str) -> str:
    """Normalize free-form text before repeated-message comparisons."""
    compact = re.sub(r"\s+", "", message.strip().lower())
    compact = re.sub(r"[，。！？、,.!?；;：:]", "", compact)
    return compact


def extract_keyword_tags(message: str, max_keywords: int = 5) -> str:
    """Extract a few readable tags for storage and future retrieval."""
    seen: list[str] = []

    for token in TOKEN_PATTERN.findall(message):
        normalized = token.strip().lower()
        if not normalized:
            continue
        if normalized in STOPWORDS:
            continue
        if len(normalized) == 1 and not normalized.isdigit():
            continue
        if normalized not in seen:
            seen.append(normalized)
        if len(seen) >= max_keywords:
            break

    return ", ".join(seen)


def detect_repeated_flag(message: str, recent_logs: Sequence[ChatLog]) -> bool:
    """Mark a message as repeated if a similar user text appeared in the last few turns."""
    normalized = normalize_message_text(message)
    if not normalized:
        return False

    recent_user_logs = [log for log in recent_logs if log.role == "user"][-3:]

    for log in reversed(recent_user_logs):
        if memory_service.is_similar_user_message(log.message, message):
            return True

    return False


def analyze_user_message(message: str, recent_logs: Sequence[ChatLog]) -> dict[str, object]:
    """Generate storage metadata for a user message."""
    return {
        "keyword_tags": extract_keyword_tags(message),
        "repeated_flag": detect_repeated_flag(message, recent_logs),
    }


def analyze_assistant_message(message: str) -> dict[str, object]:
    """Generate storage metadata for an assistant message."""
    return {
        "keyword_tags": extract_keyword_tags(message),
        "repeated_flag": False,
    }


def build_memory_digest(profile: UserProfile, chat_logs: Sequence[ChatLog]) -> dict[str, object]:
    """Build a short memory digest through the dedicated memory-summary service."""
    return memory_service.build_memory_summary(profile, chat_logs)
