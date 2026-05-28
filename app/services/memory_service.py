"""Memory guidance helpers and compact memory-summary extraction for Alzheimer support."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal, Sequence

from app.init_db import initialize_database
from app.models.chat_log import ChatLog
from app.models.user_profile import UserProfile
from app.services import profile_service
from app.utils.context_builder import build_profile_context

CURRENT_PROFILE: dict[str, object] = {}

AnchorKind = Literal["recent", "family", "life", "preference", "place"]

LOW_SIGNAL_EXACT = {"嗯", "恩", "哦", "好", "好的", "行", "可以", "知道了", "没有"}
FORGETFUL_HINTS = ("忘了", "我忘了", "记不清", "想不起来")
UNCERTAIN_HINTS = ("不知道", "不记得", "说不上来")
CHALLENGE_HINTS = ("为什么只有这一句话", "怎么只有一句话", "你在搞笑吗", "你是谁")
RECENT_ANCHOR_BLOCK_HINTS = ("不要老是", "别老", "别总", "一直在提", "总提", "为什么", "怎么")
FAMILY_HINTS = ("家人", "家里", "女儿", "儿子", "爸爸", "妈妈", "老伴", "丈夫", "爱人")
LIFE_HINTS = ("以前", "过去", "经历", "工作", "年轻", "小时候", "上班")
PREFERENCE_HINTS = ("喜欢", "爱好", "想听", "想吃", "偏好")
PLACE_HINTS = ("家乡", "哪里", "地方", "老房子", "住", "街道")
SUMMARY_RELATION_HINTS = ("女儿", "儿子", "妈妈", "爸爸", "老伴", "丈夫", "爱人", "家人", "姐姐", "哥哥", "妹妹", "弟弟")
SUMMARY_LIFE_HINTS = ("以前", "过去", "经历", "工作", "年轻", "小时候", "上班", "学校", "商场", "夫子庙")
SUMMARY_PREFERENCE_HINTS = ("喜欢", "爱好", "想听", "想吃", "偏好", "老歌", "评弹", "散步")
SUMMARY_PLACE_HINTS = ("家乡", "南京", "上海", "杭州", "苏州", "地方", "老家", "夫子庙")


@dataclass(slots=True)
class MemoryAnchor:
    """One familiar anchor used to gently continue the conversation."""

    kind: AnchorKind
    text: str


def _get_active_profile() -> UserProfile:
    """Resolve the latest profile so older imports keep working after the refactor."""
    initialize_database()
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    CURRENT_PROFILE.clear()
    CURRENT_PROFILE.update(profile.to_dict())
    return profile


def build_memory_context() -> str:
    """Expose profile context in the original helper shape."""
    profile = _get_active_profile()
    return build_profile_context(profile)


def generate_memory_reply(user_message: str) -> str:
    """Delegate legacy reply generation to the new chat orchestration layer."""
    from app.services import chat_service

    profile = _get_active_profile()
    result = chat_service.generate_chat_reply(profile.id, user_message, "alzheimer")
    CURRENT_PROFILE.clear()
    CURRENT_PROFILE.update(result["profile"])
    return result["reply"]


def _normalize_text(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if ch not in " ，。！？、,.!?；;：:\n\t")


def _split_text(text: str) -> list[str]:
    pieces = (
        text.replace("；", "，")
        .replace("。", "，")
        .replace("、", "，")
        .replace("\n", "，")
        .split("，")
    )
    return [piece.strip() for piece in pieces if piece.strip()]


def _split_summary_pieces(text: str) -> list[str]:
    """Split free-form notes into short summary-friendly pieces."""
    return [
        piece.strip()
        for piece in re.split(r"[，,；;。！？!\?\n]", str(text or ""))
        if piece.strip()
    ]


def _summary_short_text(text: str, max_length: int = 18) -> str:
    """Shorten summary snippets so they stay readable in prompts and UI."""
    value = str(text or "").strip()
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def _summary_unique_items(items: Sequence[str], limit: int = 3) -> list[str]:
    """Keep a stable unique subset of summary items."""
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = _summary_short_text(item)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def _summary_contains_hint(text: str, hints: Sequence[str]) -> bool:
    """Check whether one text piece belongs to a coarse memory category."""
    normalized = _normalize_text(text)
    return any(_normalize_text(hint) in normalized for hint in hints)


def _collect_user_summary_pieces(chat_logs: Sequence[ChatLog]) -> list[str]:
    """Collect reusable user-side snippets from recent chat logs."""
    pieces: list[str] = []
    for log in chat_logs:
        if log.role != "user":
            continue
        pieces.extend(_split_summary_pieces(log.message))
        pieces.extend(_split_summary_pieces(log.keyword_tags))
    return [piece for piece in pieces if piece]


def _select_summary_items(primary: Sequence[str], fallback: Sequence[str], limit: int = 3) -> list[str]:
    """Prefer recent extracted items, then fill from stored profile data."""
    result = _summary_unique_items(primary, limit=limit)
    if len(result) >= limit:
        return result
    merged = [*result, *fallback]
    return _summary_unique_items(merged, limit=limit)


def _build_follow_up_topics(
    mentioned_people: Sequence[str],
    place_topics: Sequence[str],
    life_topics: Sequence[str],
    preference_topics: Sequence[str],
) -> list[str]:
    """Pick the easiest familiar anchors to continue from next."""
    return _summary_unique_items(
        [
            *mentioned_people,
            *place_topics,
            *life_topics,
            *preference_topics,
        ],
        limit=3,
    )


def _is_clean_family_piece(piece: str) -> bool:
    """Keep family mentions short and usable in the compact summary."""
    text = str(piece or "").strip()
    if not text:
        return False
    if not _summary_contains_hint(text, SUMMARY_RELATION_HINTS):
        return False
    if len(text) > 12:
        return False
    if any(block in text for block in ("吗", "谁", "不是", "为什么", "怎么")):
        return False
    return True


def build_memory_summary(profile: UserProfile, chat_logs: Sequence[ChatLog]) -> dict[str, object]:
    """Build a short long-term memory digest from profile and recent chat patterns."""
    user_pieces = _collect_user_summary_pieces(chat_logs)
    repeated_logs = [log for log in chat_logs if log.role == "user" and log.repeated_flag]
    repeated_pieces = [
        piece
        for log in repeated_logs
        for piece in [*_split_summary_pieces(log.keyword_tags), *_split_summary_pieces(log.message)]
    ]

    family_primary = [piece for piece in user_pieces if _is_clean_family_piece(piece)]
    life_primary = [piece for piece in user_pieces if _summary_contains_hint(piece, SUMMARY_LIFE_HINTS)]
    preference_primary = [piece for piece in user_pieces if _summary_contains_hint(piece, SUMMARY_PREFERENCE_HINTS)]
    place_primary = [piece for piece in user_pieces if _summary_contains_hint(piece, SUMMARY_PLACE_HINTS)]

    family_fallback = _split_summary_pieces(profile.family_info)
    life_fallback = _split_summary_pieces(profile.life_events)
    preference_fallback = _split_summary_pieces(profile.preferences)
    place_fallback = _split_summary_pieces(profile.hometown)

    mentioned_people = _select_summary_items(family_primary, family_fallback, limit=3)
    life_topics = _select_summary_items(life_primary, life_fallback, limit=3)
    preference_topics = _select_summary_items(preference_primary, preference_fallback, limit=3)
    place_topics = _select_summary_items(place_primary, place_fallback, limit=2)
    repeated_topics = _summary_unique_items(repeated_pieces, limit=2)
    follow_up_topics = _build_follow_up_topics(
        mentioned_people,
        place_topics,
        life_topics,
        preference_topics,
    )

    summary_parts: list[str] = []
    if mentioned_people:
        summary_parts.append(f"常提到的人有{'、'.join(mentioned_people)}")
    if place_topics:
        summary_parts.append(f"熟悉地点会回到{'、'.join(place_topics)}")
    if life_topics:
        summary_parts.append(f"常聊经历有{'、'.join(life_topics)}")
    if preference_topics:
        summary_parts.append(f"偏好线索里有{'、'.join(preference_topics)}")
    if repeated_topics:
        summary_parts.append(f"重复会回到{'、'.join(repeated_topics)}")

    return {
        "mentioned_people": mentioned_people,
        "life_topics": life_topics,
        "preference_topics": preference_topics,
        "place_topics": place_topics,
        "repeated_topics": repeated_topics,
        "follow_up_topics": follow_up_topics,
        "summary": (
            f"{'；'.join(summary_parts[:3])}。"
            if summary_parts
            else "现在还没有足够的历史内容，先从熟悉的人和旧日线索慢慢积累。"
        ),
    }


def _extract_keywords(text: str) -> set[str]:
    return {piece for piece in _split_text(text) if len(piece) >= 2}


def is_similar_user_message(message_a: str, message_b: str) -> bool:
    """Treat repeated or near-repeated user questions as the same conversational thread."""
    normalized_a = _normalize_text(message_a)
    normalized_b = _normalize_text(message_b)

    if not normalized_a or not normalized_b:
        return False
    if normalized_a == normalized_b:
        return True

    shorter = normalized_a if len(normalized_a) <= len(normalized_b) else normalized_b
    longer = normalized_b if shorter == normalized_a else normalized_a
    if shorter in longer:
        anchor_kind_a = _infer_requested_anchor_kind(message_a)
        anchor_kind_b = _infer_requested_anchor_kind(message_b)
        if len(shorter) >= 5:
            return True
        if anchor_kind_a is not None and anchor_kind_a == anchor_kind_b:
            return True

    keywords_a = _extract_keywords(message_a)
    keywords_b = _extract_keywords(message_b)
    if keywords_a and keywords_b and keywords_a.intersection(keywords_b):
        return True

    anchor_kind_a = _infer_requested_anchor_kind(message_a)
    anchor_kind_b = _infer_requested_anchor_kind(message_b)
    if anchor_kind_a is not None and anchor_kind_a == anchor_kind_b:
        if any(hint in message_a for hint in ("来着", "谁", "以前", "喜欢")) and any(
            hint in message_b for hint in ("来着", "谁", "以前", "喜欢")
        ):
            return True

    similarity = SequenceMatcher(None, normalized_a, normalized_b).ratio()
    if similarity < 0.72:
        return False

    if len(normalized_a) <= 4 or len(normalized_b) <= 4:
        anchor_kind_a = _infer_requested_anchor_kind(message_a)
        anchor_kind_b = _infer_requested_anchor_kind(message_b)
        return anchor_kind_a is not None and anchor_kind_a == anchor_kind_b

    return True


def _shorten(text: str, max_length: int = 18) -> str:
    value = text.strip()
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def _pick_variant(seed_text: str, options: Sequence[str]) -> str:
    if not options:
        return ""
    index = sum(ord(ch) for ch in seed_text) % len(options)
    return options[index]


def classify_user_message(message: str) -> str:
    """Classify user input into lightweight conversational scenarios."""
    stripped = message.strip()
    normalized = _normalize_text(stripped)

    if not normalized:
        return "brief"
    if any(hint in stripped for hint in CHALLENGE_HINTS):
        return "challenge"
    if any(hint in normalized for hint in FORGETFUL_HINTS):
        return "forgetful"
    if any(hint in normalized for hint in UNCERTAIN_HINTS):
        return "uncertain"
    if normalized in LOW_SIGNAL_EXACT:
        return "brief_ack"
    if len(normalized) <= 3:
        return "brief"
    if "？" not in stripped and len(normalized) <= 8:
        return "unclear"
    return "normal"


def is_low_signal_message(message: str) -> bool:
    """Expose whether the current user message needs recall guidance."""
    return classify_user_message(message) != "normal"


def _infer_requested_anchor_kind(message: str) -> AnchorKind | None:
    normalized = _normalize_text(message)

    if any(hint in normalized for hint in FAMILY_HINTS):
        return "family"
    if any(hint in normalized for hint in LIFE_HINTS):
        return "life"
    if any(hint in normalized for hint in PREFERENCE_HINTS):
        return "preference"
    if any(hint in normalized for hint in PLACE_HINTS):
        return "place"
    return None


def _is_meaningful_recent_message(message: str, current_message: str) -> bool:
    normalized = _normalize_text(message)
    current = _normalize_text(current_message)
    if not normalized or normalized == current:
        return False
    if _infer_requested_anchor_kind(message) is not None:
        return True
    return classify_user_message(message) == "normal"


def _recent_messages_blob(recent_logs: Sequence[ChatLog], limit: int = 6) -> str:
    """Combine recent messages so repeated anchors can cool down naturally."""
    recent_messages = [log.message for log in recent_logs[-limit:] if log.message]
    return " ".join(_normalize_text(message) for message in recent_messages)


def _anchor_recently_used(anchor_text: str, recent_logs: Sequence[ChatLog]) -> bool:
    """Check whether one stored anchor was mentioned very recently."""
    normalized_anchor = _normalize_text(anchor_text)
    if not normalized_anchor:
        return False
    recent_blob = _recent_messages_blob(recent_logs)
    return normalized_anchor in recent_blob


def _pick_profile_piece(raw_text: str, recent_logs: Sequence[ChatLog]) -> str:
    """Prefer a profile snippet that has not just been repeated in nearby turns."""
    pieces = _split_text(raw_text)
    if not pieces:
        return ""

    for piece in pieces:
        if not _anchor_recently_used(piece, recent_logs):
            return piece
    return pieces[0]


def _is_recent_anchor_candidate(message: str, current_message: str) -> bool:
    """Only keep recent messages that can safely become continuation anchors."""
    if not _is_meaningful_recent_message(message, current_message):
        return False

    stripped = message.strip()
    normalized = _normalize_text(stripped)
    if not normalized:
        return False
    if any(hint in stripped for hint in RECENT_ANCHOR_BLOCK_HINTS):
        return False
    if any(marker in stripped for marker in ("？", "?", "谁", "吗")):
        return False

    inferred_kind = _infer_requested_anchor_kind(stripped)
    if inferred_kind is not None:
        return True

    return len(normalized) <= 12 and classify_user_message(stripped) == "normal"


def _infer_recent_anchor_kind(recent_logs: Sequence[ChatLog], current_message: str) -> AnchorKind | None:
    """Infer the most recent usable topic kind from nearby user turns."""
    for log in reversed(recent_logs):
        if log.role != "user":
            continue
        if not _is_recent_anchor_candidate(log.message, current_message):
            continue
        inferred = _infer_requested_anchor_kind(log.message)
        if inferred is not None:
            return inferred
    return None


def _profile_anchor_order(
    recent_logs: Sequence[ChatLog],
    current_message: str,
    preferred_kind: AnchorKind | None,
) -> list[AnchorKind]:
    """Build a calmer fallback order so one family name does not dominate."""
    if preferred_kind is not None:
        return [preferred_kind]

    recent_kind = _infer_recent_anchor_kind(recent_logs, current_message)
    ordered = [recent_kind, "family", "place", "life", "preference"]
    result: list[AnchorKind] = []
    for kind in ordered:
        if kind is None or kind in result:
            continue
        result.append(kind)
    return result


def _message_matches_anchor_kind(message: str, anchor_kind: AnchorKind | None) -> bool:
    inferred_kind = _infer_requested_anchor_kind(message)
    if inferred_kind is None or anchor_kind is None:
        return False
    return inferred_kind == anchor_kind


def _select_recent_anchor(
    recent_logs: Sequence[ChatLog],
    current_message: str,
    preferred_kind: AnchorKind | None = None,
) -> MemoryAnchor | None:
    if preferred_kind is not None:
        for log in reversed(recent_logs):
            if log.role != "user":
                continue
            if not _is_recent_anchor_candidate(log.message, current_message):
                continue
            if not _message_matches_anchor_kind(log.message, preferred_kind):
                continue
            return MemoryAnchor(kind="recent", text=_shorten(log.message, 18))

    for log in reversed(recent_logs):
        if log.role != "user":
            continue
        if not _is_recent_anchor_candidate(log.message, current_message):
            continue
        return MemoryAnchor(kind="recent", text=_shorten(log.message, 18))
    return None


def _select_profile_anchor(
    profile: UserProfile,
    recent_logs: Sequence[ChatLog],
    current_message: str,
    preferred_kind: AnchorKind | None = None,
) -> MemoryAnchor | None:
    mapping: dict[AnchorKind, str] = {
        "family": profile.family_info,
        "life": profile.life_events,
        "preference": profile.preferences,
        "place": profile.hometown or profile.notes,
    }

    order = _profile_anchor_order(recent_logs, current_message, preferred_kind)
    for kind in order:
        raw_text = mapping.get(kind, "")
        piece = _pick_profile_piece(raw_text, recent_logs)
        if piece:
            return MemoryAnchor(kind=kind, text=_shorten(piece, 18))

    return None


def choose_memory_anchor(
    profile: UserProfile,
    recent_logs: Sequence[ChatLog],
    user_message: str,
    *,
    prefer_recent: bool = True,
) -> MemoryAnchor | None:
    """Choose one familiar anchor, prioritizing recent topics before profile fallbacks."""
    preferred_kind = _infer_requested_anchor_kind(user_message)

    # When the user explicitly mentions family, past experiences, preferences,
    # or place cues, stay with that theme before falling back to unrelated topics.
    if preferred_kind is not None:
        if prefer_recent:
            themed_recent_anchor = _select_recent_anchor(recent_logs, user_message, preferred_kind)
            if themed_recent_anchor is not None:
                return themed_recent_anchor

        preferred_profile_anchor = _select_profile_anchor(profile, recent_logs, user_message, preferred_kind)
        if preferred_profile_anchor is not None:
            return preferred_profile_anchor

    if prefer_recent:
        recent_anchor = _select_recent_anchor(recent_logs, user_message)
        if recent_anchor is not None:
            return recent_anchor

    profile_anchor = _select_profile_anchor(profile, recent_logs, user_message, None)
    if profile_anchor is not None:
        return profile_anchor

    if not prefer_recent:
        return _select_recent_anchor(recent_logs, user_message)

    return None


def _build_anchor_prompt(anchor: MemoryAnchor, seed_text: str) -> str:
    if anchor.kind == "recent":
        return _pick_variant(
            seed_text,
            [
                f"如果愿意，我们就顺着刚才提到的“{anchor.text}”继续慢慢聊。",
                f"要不我们先不换话题，就从刚才说到的“{anchor.text}”慢慢想一想。",
                f"我们也可以先沿着“{anchor.text}”这条线索接着往下说。",
            ],
        )

    if anchor.kind == "family":
        return _pick_variant(
            seed_text,
            [
                f"如果愿意，我们可以先从{anchor.text}慢慢说起。",
                f"要不要先想想和{anchor.text}在一起时，最熟悉的一件小事？",
                f"我们也可以先聊聊{anchor.text}，看看会不会带出更多熟悉的画面。",
            ],
        )

    if anchor.kind == "life":
        return _pick_variant(
            seed_text,
            [
                f"如果愿意，我们可以先从{anchor.text}那段日子慢慢想起。",
                f"要不要先说说和{anchor.text}有关的一件熟悉小事？",
                f"我们也可以顺着{anchor.text}这段经历，慢慢看看会想起什么。",
            ],
        )

    if anchor.kind == "preference":
        return _pick_variant(
            seed_text,
            [
                f"也可以先从{anchor.text}这样让人安心的事情说起。",
                f"如果愿意，我们就从{anchor.text}这些熟悉偏好慢慢聊。",
                f"我们也可以先聊聊{anchor.text}，不用急着一下子想很多。",
            ],
        )

    return _pick_variant(
        seed_text,
        [
            f"我们也可以先想想{anchor.text}，看看那里有没有熟悉的画面。",
            f"如果愿意，我们就先从{anchor.text}这样的熟悉地方慢慢说起。",
            f"要不要先顺着{anchor.text}这条线索，轻轻回想一下？",
        ],
    )


def build_memory_guidance_reply(
    profile: UserProfile,
    recent_logs: Sequence[ChatLog],
    user_message: str,
) -> str | None:
    """Build a gentle recall prompt for short, unclear, or uncertain user messages."""
    scenario = classify_user_message(user_message)
    if scenario == "normal":
        return None

    anchor = choose_memory_anchor(profile, recent_logs, user_message, prefer_recent=True)

    opener_map = {
        "forgetful": "想不起来也没关系。",
        "uncertain": "不知道也没关系。",
        "brief_ack": "嗯，我们慢慢来就好。",
        "brief": "没关系，我们不用一下子说很多。",
        "unclear": "我们可以不用急着回答得很完整。",
    }

    opener = opener_map.get(scenario, "没关系，我们慢慢来就好。")
    if anchor is None:
        return opener

    return f"{opener}{_build_anchor_prompt(anchor, user_message)}"


def build_follow_up_guidance(
    profile: UserProfile,
    recent_logs: Sequence[ChatLog],
    user_message: str,
) -> str | None:
    """Add one soft follow-up line so replies keep the conversation gently moving."""
    if is_low_signal_message(user_message):
        return None

    anchor = choose_memory_anchor(profile, recent_logs, user_message, prefer_recent=True)
    if anchor is None:
        return None
    return _build_anchor_prompt(anchor, user_message)


def build_repeated_question_guidance(
    profile: UserProfile,
    recent_logs: Sequence[ChatLog],
    user_message: str,
) -> str:
    """Return a calm, non-testing follow-up for repeated questions."""
    anchor = choose_memory_anchor(profile, recent_logs, user_message, prefer_recent=True)
    if anchor is None:
        return "没关系，我们就沿着刚才那点熟悉的线索慢慢说。"
    return f"没关系，我们刚刚也聊到这里了。{_build_anchor_prompt(anchor, user_message)}"
