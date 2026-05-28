"""Conversation state detection and mock fallback helpers.

The real LLM path now owns most of the final wording. This module keeps only
lightweight state tagging plus a local fallback reply generator for cases where
the remote model is unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import random
import re
from typing import Literal, Sequence

from app.models.chat_log import ChatLog
from app.models.user_profile import UserProfile
from app.services import conversation_phrases, memory_service

Topic = Literal["family", "life", "preference", "place", "general"]
CareScenario = Literal[
    "medication_confusion",
    "medication_uncertainty",
    "fear_anxiety",
    "anxiety_abandonment",
    "going_home",
    "disorientation_going_home",
    "wandering_risk",
    "wandering_intent",
    "repeated_question",
    "repeated_question_xiaoyu",
    "self_awareness_repeated_question",
    "person_recognition",
    "suspicion_or_delusion",
    "sensitive_deceased_spouse_topic",
    "deceased_spouse_sensitive",
    "date_time_confusion",
    "general",
]
InputKind = Literal[
    "need_request",
    "clarification",
    "comment",
    "memory_question",
    "confusion",
    "emotional",
    "short_input",
    "repeat_question",
    "topic_followup",
    "general",
]
Strategy = Literal[
    "normal_chat",
    "familiar_guidance",
    "light_support",
    "repeat_soft_response",
    "complaint_repair",
    "clarification_repair",
    "current_need_response",
]

FAMILY_HINTS = ("家人", "家里", "女儿", "儿子", "爸爸", "妈妈", "老伴", "丈夫", "爱人")
LIFE_HINTS = ("以前", "过去", "经历", "工作", "年轻", "小时候", "上班")
PREFERENCE_HINTS = ("喜欢", "爱好", "想吃", "想听", "偏好")
PLACE_HINTS = ("家乡", "哪里", "地方", "老房子", "住", "街道")
COMPLAINT_HINTS = ("为什么只有一句话", "为什么只有这一句话", "怎么只有一句话", "你在搞笑吗")
RECENT_TOPIC_BLOCK_HINTS = ("不要老是", "别老", "别总", "一直在提", "总提", "为什么", "怎么")
CLARIFICATION_HINTS = ("你再说什么", "你说什么", "什么", "啊", "听不清", "没听懂", "你在说啥", "那是谁", "什么意思")
MEMORY_QUESTION_HINTS = ("我是谁", "我叫什么", "我的名字", "我女儿是谁", "我儿子是谁", "我妈妈是谁", "我爸爸是谁", "我老伴是谁")
CONFUSION_HINTS = ("我现在在哪", "现在在哪", "我在哪", "这是哪", "这是哪里")
EMOTIONAL_HINTS = ("你在搞笑吗", "不对", "不是", "你别乱说", "你到底在说什么")
COMMENT_HINTS = ("好单位", "是啊", "对", "嗯对", "是吗", "对啊", "挺好", "不错")
CURRENT_NEED_HINTS: dict[str, tuple[str, ...]] = {
    "hungry": ("我饿了", "饿了"),
    "tired": ("我累了", "累了"),
    "sleepy": ("我困了", "困了", "我想睡觉", "想睡觉"),
    "discomfort": ("我不舒服", "不舒服", "难受"),
    "food": ("我想吃东西", "想吃东西", "想吃点", "吃点东西"),
}
ANCHOR_PRIORITY_KINDS = {"brief", "brief_ack", "forgetful", "uncertain"}


@dataclass(slots=True)
class ConversationState:
    """Per-turn user state detected from the message and recent logs."""

    raw_message: str
    normalized_message: str
    input_kind: InputKind
    memory_guidance_active: bool
    short_input: bool
    short_input_kind: str | None
    repeat_question: bool
    clarification_request: bool
    current_need: str | None
    memory_question: bool
    confusion: bool
    emotional: bool
    family_topic: bool
    life_topic: bool
    preference_topic: bool
    place_topic: bool
    complaint_tone: bool
    current_topic: Topic
    care_scenario: CareScenario


@dataclass(slots=True)
class ConversationContext:
    """Context used by the expression layer to compose the final reply."""

    profile: UserProfile
    recent_logs: Sequence[ChatLog]
    user_message: str
    state: ConversationState
    last_reply: str = ""


def _normalize_text(text: str) -> str:
    """Normalize free-form text for small comparisons."""
    return "".join(ch for ch in text.strip().lower() if ch not in " ，。！？、,.!?；;：:\n\t")


def _split_text(text: str) -> list[str]:
    """Split stored profile text into short reusable pieces."""
    pieces = (
        str(text or "")
        .replace("；", "，")
        .replace("。", "，")
        .replace("、", "，")
        .replace("\n", "，")
        .split("，")
    )
    return [piece.strip() for piece in pieces if piece.strip()]


def _trim(text: str) -> str:
    """Trim trailing punctuation before reusing profile text."""
    return str(text or "").rstrip("。！？!?；;，, ")


def _message_has_hint(message: str, hints: Sequence[str]) -> bool:
    normalized = _normalize_text(message)
    return any(hint in normalized for hint in hints)


def _infer_topic_from_message(message: str) -> Topic | None:
    """Infer the topic the user is currently touching."""
    if _message_has_hint(message, FAMILY_HINTS):
        return "family"
    if _message_has_hint(message, LIFE_HINTS):
        return "life"
    if _message_has_hint(message, PREFERENCE_HINTS):
        return "preference"
    if _message_has_hint(message, PLACE_HINTS):
        return "place"
    return None


def _infer_recent_topic(recent_logs: Sequence[ChatLog], current_message: str) -> Topic | None:
    """Look back a few turns to keep the topic thread stable."""
    for log in reversed(recent_logs):
        if log.role != "user":
            continue
        if not log.message.strip():
            continue
        if _normalize_text(log.message) == _normalize_text(current_message):
            continue
        if any(hint in log.message for hint in RECENT_TOPIC_BLOCK_HINTS):
            continue
        topic = _infer_topic_from_message(log.message)
        if topic is not None:
            return topic
        if memory_service.classify_user_message(log.message) in {"brief", "brief_ack", "forgetful", "uncertain", "challenge"}:
            continue
    return None


def _detect_clarification_request(message: str) -> bool:
    """Recognize when the user wants the assistant to say it again more clearly."""
    normalized = _normalize_text(message)
    return any(_normalize_text(hint) == normalized or _normalize_text(hint) in normalized for hint in CLARIFICATION_HINTS)


def _detect_current_need(message: str) -> str | None:
    """Recognize immediate needs so the reply does not get hijacked by memory anchors."""
    normalized = _normalize_text(message)
    for need, hints in CURRENT_NEED_HINTS.items():
        if any(_normalize_text(hint) in normalized for hint in hints):
            return need
    return None


def _detect_memory_question(message: str) -> bool:
    """Recognize direct identity and family-memory questions."""
    normalized = _normalize_text(message)
    return any(_normalize_text(hint) in normalized for hint in MEMORY_QUESTION_HINTS)


def _detect_confusion(message: str) -> bool:
    """Recognize orientation confusion such as asking where they are."""
    normalized = _normalize_text(message)
    return any(_normalize_text(hint) in normalized for hint in CONFUSION_HINTS)


def _detect_emotional_input(message: str) -> bool:
    """Recognize mild frustration or emotional pushback."""
    normalized = _normalize_text(message)
    return any(_normalize_text(hint) in normalized for hint in EMOTIONAL_HINTS)


def _detect_care_scenario(message: str, repeat_question: bool) -> CareScenario:
    """Detect high-frequency caregiver-risk scenes before generic memory guidance."""
    normalized = _normalize_text(message)
    if any(token in normalized for token in ("偷", "被偷", "拿走", "不见了", "谁拿了", "东西没了", "钱没了")):
        return "suspicion_or_delusion"
    if any(token in normalized for token in ("没吃药", "药吃过", "吃药了吗", "是不是还没吃药", "忘记药")):
        return "medication_uncertainty"
    if any(token in normalized for token in ("我要回家", "这里是哪里", "这是哪里", "我在哪", "现在在哪", "这不是我家", "这里不是我家")):
        return "disorientation_going_home"
    if any(token in normalized for token in ("出去走走", "出门走走", "我要出去", "夜里出去", "晚上出去")):
        return "wandering_intent"
    if any(token in normalized for token in ("我害怕", "有点害怕", "我不安心", "不安心", "怕", "没人管我", "被丢下")):
        return "anxiety_abandonment"
    if any(token in normalized for token in ("老王怎么还没回来", "我老伴去哪了", "老王呢", "老伴去哪了", "他怎么还没回来")):
        return "deceased_spouse_sensitive"
    if any(token in normalized for token in ("今天几号", "今天是几号", "现在几点", "今天几月")):
        return "date_time_confusion"
    if any(token in normalized for token in ("这个人是谁", "那个人是谁", "这是谁", "他是谁", "她是谁")):
        return "person_recognition"
    if "刚刚是不是问过" in normalized:
        return "self_awareness_repeated_question"
    if "小雨什么时候回来" in normalized:
        return "repeated_question_xiaoyu"
    if repeat_question:
        return "repeated_question"
    return "general"


def _detect_comment_input(message: str) -> bool:
    """Recognize short evaluative comments that should be answered directly."""
    normalized = _normalize_text(message)
    return any(_normalize_text(hint) == normalized or _normalize_text(hint) in normalized for hint in COMMENT_HINTS)


def _should_enable_memory_guidance(
    *,
    short_kind: str,
    current_need: str | None,
    clarification_request: bool,
    memory_question: bool,
    confusion: bool,
    emotional: bool,
    comment_input: bool,
    current_topic: Topic,
) -> bool:
    """Keep memory guidance as an auxiliary mode instead of the default behavior."""
    if current_need or clarification_request or confusion or emotional or comment_input:
        return False
    if short_kind in {"forgetful", "uncertain", "brief_ack", "brief"}:
        return True
    if memory_question:
        return True
    if current_topic != "general":
        return True
    return False


def _detect_repeat_question(message: str, recent_logs: Sequence[ChatLog]) -> bool:
    """Reuse the existing similarity helper to detect repeated user questions."""
    recent_user_logs = [log for log in recent_logs if log.role == "user"][-3:]
    for log in reversed(recent_user_logs):
        if memory_service.is_similar_user_message(log.message, message):
            return True
    return False


def detect_user_state(message: str, recent_logs: Sequence[ChatLog]) -> ConversationState:
    """Detect user tone, current topic, and repetition before choosing a strategy."""
    short_kind = memory_service.classify_user_message(message)
    clarification_request = _detect_clarification_request(message)
    current_need = _detect_current_need(message)
    memory_question = _detect_memory_question(message)
    confusion = _detect_confusion(message)
    emotional = _detect_emotional_input(message)
    comment_input = _detect_comment_input(message)
    repeat_question = _detect_repeat_question(message, recent_logs)
    care_scenario = _detect_care_scenario(message, repeat_question)

    direct_topic = _infer_topic_from_message(message)
    if clarification_request or current_need:
        current_topic = direct_topic or "general"
    else:
        current_topic = direct_topic or _infer_recent_topic(recent_logs, message) or "general"

    input_kind: InputKind = "general"
    if current_need is not None:
        input_kind = "need_request"
    elif clarification_request:
        input_kind = "clarification"
    elif comment_input:
        input_kind = "comment"
    elif memory_question:
        input_kind = "memory_question"
    elif confusion:
        input_kind = "confusion"
    elif emotional:
        input_kind = "emotional"
    elif repeat_question:
        input_kind = "repeat_question"
    elif short_kind in ANCHOR_PRIORITY_KINDS or short_kind in {"brief", "brief_ack"}:
        input_kind = "short_input"
    elif current_topic != "general":
        input_kind = "topic_followup"

    memory_guidance_active = _should_enable_memory_guidance(
        short_kind=short_kind,
        current_need=current_need,
        clarification_request=clarification_request,
        memory_question=memory_question,
        confusion=confusion,
        emotional=emotional,
        comment_input=comment_input,
        current_topic=current_topic,
    )

    return ConversationState(
        raw_message=message,
        normalized_message=_normalize_text(message),
        input_kind=input_kind,
        memory_guidance_active=memory_guidance_active,
        short_input=short_kind in ANCHOR_PRIORITY_KINDS,
        short_input_kind=None if short_kind == "normal" else short_kind,
        repeat_question=repeat_question,
        clarification_request=clarification_request,
        current_need=current_need,
        memory_question=memory_question,
        confusion=confusion,
        emotional=emotional,
        family_topic=_message_has_hint(message, FAMILY_HINTS),
        life_topic=_message_has_hint(message, LIFE_HINTS),
        preference_topic=_message_has_hint(message, PREFERENCE_HINTS),
        place_topic=_message_has_hint(message, PLACE_HINTS),
        complaint_tone=any(hint in message for hint in COMPLAINT_HINTS),
        current_topic=current_topic,
        care_scenario=care_scenario,
    )


def decide_strategy(state: ConversationState) -> Strategy:
    """Map detected state to a coarse response-focus label.

    The return value is now only a lightweight tag. It should not dictate exact
    wording for the real LLM path.
    """
    if state.clarification_request:
        return "clarification_repair"
    if state.current_need is not None:
        return "current_need_response"
    if state.input_kind == "comment":
        return "normal_chat"
    if state.memory_question:
        return "normal_chat"
    if state.confusion:
        return "light_support"
    if state.emotional:
        return "complaint_repair"
    if state.complaint_tone:
        return "complaint_repair"
    if state.repeat_question:
        return "repeat_soft_response"
    if state.short_input:
        if state.current_topic != "general":
            return "familiar_guidance"
        return "light_support"
    if state.family_topic or state.life_topic or state.preference_topic or state.place_topic:
        return "normal_chat"
    return "normal_chat"


def _recent_assistant_messages(recent_logs: Sequence[ChatLog], limit: int = 3) -> list[str]:
    """Return the most recent assistant messages for cooldown checks."""
    return [log.message for log in recent_logs if log.role == "assistant"][-limit:]


def get_last_assistant_reply(recent_logs: Sequence[ChatLog]) -> str:
    """Return the previous assistant reply so openings can avoid echoing it."""
    assistant_messages = _recent_assistant_messages(recent_logs, limit=1)
    if not assistant_messages:
        return ""
    return assistant_messages[-1]


def _contains_soft_marker(text: str) -> bool:
    """Check whether one reply fragment counts as a soft reassurance phrase."""
    return any(marker in text for marker in conversation_phrases.SOFT_MARKERS)


def _soft_cooldown_active(recent_logs: Sequence[ChatLog]) -> bool:
    """Prevent soft reassurance from appearing on consecutive assistant turns."""
    assistant_messages = _recent_assistant_messages(recent_logs, limit=2)
    if not assistant_messages:
        return False
    return _contains_soft_marker(assistant_messages[-1])


def _pick_one(
    options: Sequence[str],
    recent_logs: Sequence[ChatLog],
    *,
    last_reply: str = "",
    avoid_soft: bool = False,
    fallback: str = "",
) -> str:
    """Pick one fragment while avoiding very recent repetition when possible."""
    if not options:
        return fallback

    recent_text = " ".join([*_recent_assistant_messages(recent_logs, limit=3), last_reply])
    filtered = [option for option in options if option and option not in recent_text]
    if avoid_soft:
        filtered = [option for option in filtered if not _contains_soft_marker(option)]

    pool = filtered or [option for option in options if option]
    if avoid_soft:
        non_soft_pool = [option for option in pool if not _contains_soft_marker(option)]
        if non_soft_pool:
            pool = non_soft_pool

    if not pool:
        return fallback

    return random.choice(pool)


def _assistant_reply_similarity(text_a: str, text_b: str) -> float:
    """Estimate whether two assistant replies are effectively saying the same thing."""
    normalized_a = _normalize_text(text_a)
    normalized_b = _normalize_text(text_b)
    if not normalized_a or not normalized_b:
        return 0.0
    if normalized_a == normalized_b:
        return 1.0
    return SequenceMatcher(None, normalized_a, normalized_b).ratio()


def _recent_assistant_repetition_active(recent_logs: Sequence[ChatLog]) -> bool:
    """Detect when the last two assistant replies were already too similar."""
    assistant_messages = _recent_assistant_messages(recent_logs, limit=2)
    if len(assistant_messages) < 2:
        return False
    return _assistant_reply_similarity(assistant_messages[-1], assistant_messages[-2]) >= 0.82


def _extract_relation_snippet(family_info: str, relation: str) -> str:
    """Try to keep direct family answers short and natural."""
    if not family_info or relation not in family_info:
        return ""
    pattern = re.compile(rf"({relation}[^，。；;\n]*)")
    match = pattern.search(family_info)
    if not match:
        return ""
    return _trim(match.group(1))


def _format_phrase(template: str, **kwargs: str) -> str:
    """Fill a phrase template with the resolved anchor text."""
    return template.format(**kwargs)


def _build_anchor(topic: Topic, context: ConversationContext) -> tuple[Topic, str]:
    """Resolve the best familiar anchor from recent logs or stored profile fields."""
    if context.state.clarification_request or context.state.current_need is not None:
        return "general", ""

    anchor = memory_service.choose_memory_anchor(
        context.profile,
        context.recent_logs,
        context.user_message,
        prefer_recent=not context.state.complaint_tone,
    )
    if anchor is not None:
        mapped_topic: Topic = "general"
        if anchor.kind == "family":
            mapped_topic = "family"
        elif anchor.kind == "life":
            mapped_topic = "life"
        elif anchor.kind == "preference":
            mapped_topic = "preference"
        elif anchor.kind == "place":
            mapped_topic = "place"
        elif anchor.kind == "recent":
            mapped_topic = topic
        return mapped_topic, anchor.text

    profile = context.profile
    fallback_mapping = {
        "family": _split_text(profile.family_info),
        "life": _split_text(profile.life_events),
        "preference": _split_text(profile.preferences),
        "place": _split_text(profile.hometown or profile.notes),
    }
    fallback_order = [topic, "family", "place", "life", "preference"]
    seen: set[Topic] = set()
    for key in fallback_order:
        if key in seen:
            continue
        seen.add(key)
        pieces = fallback_mapping.get(key, [])
        if pieces:
            return key, _trim(pieces[0])

    return "general", ""


def _summarize_last_reply(last_reply: str) -> str:
    """Keep one short meaningful part when the user asks for clarification."""
    pieces = [piece.strip() for piece in re.split(r"[，,。！？!?；;\n]", str(last_reply or "")) if piece.strip()]
    prefixes = ("我刚刚是在说", "我刚刚说的是", "我刚刚说到", "我是在说", "我说的是")
    filtered = [
        piece[len(prefix):].strip() if piece.startswith(prefix) else piece
        for piece in pieces
        for prefix in ("",)
    ]
    normalized = []
    for piece in filtered:
        value = piece
        for prefix in prefixes:
            if value.startswith(prefix):
                value = value[len(prefix):].strip()
        if value:
            normalized.append(value)

    filtered = [
        piece for piece in normalized
        if len(piece) >= 3 and not any(piece.startswith(prefix) for prefix in ("好", "嗯", "行", "那"))
    ]
    if not filtered:
        filtered = normalized or pieces
    if not filtered:
        return "刚刚那句"
    for piece in filtered:
        if not any(marker in piece for marker in ("想到", "也可以", "就从", "我们")):
            return _trim(piece[:18])
    target = filtered[0]
    return _trim(target[:18])


def _extract_food_preference(preferences: str) -> str:
    """Pick one food-like preference if the profile contains it."""
    food_hints = ("粥", "面", "饭", "汤", "馄饨", "饺子", "牛奶", "点心", "包子", "面条")
    for piece in _split_text(preferences):
        if any(hint in piece for hint in food_hints):
            return _trim(piece)
    return ""


def _build_clarification_reply(context: ConversationContext) -> str:
    """Rephrase the previous reply instead of switching topics."""
    opening = _pick_one(
        conversation_phrases.CLARIFICATION_DIRECT_PREFIXES,
        context.recent_logs,
        last_reply=context.last_reply,
        fallback="我刚刚说的是",
    )
    focus = _summarize_last_reply(context.last_reply)
    return f"{opening}{focus}。"


def _build_current_need_reply(context: ConversationContext) -> str:
    """Respond to the user's immediate need before bringing in any familiar cue."""
    need = context.state.current_need or "discomfort"
    opening = _pick_one(
        conversation_phrases.CURRENT_NEED_OPENINGS.get(need, ()),
        context.recent_logs,
        last_reply=context.last_reply,
        fallback="那先顾着眼前这会儿。",
    )
    follow = _pick_one(
        conversation_phrases.CURRENT_NEED_FOLLOWS.get(need, ()),
        context.recent_logs,
        last_reply=context.last_reply,
        fallback="你先说现在最要紧的那一点。",
    )

    light_memory = ""
    if need in {"hungry", "food"}:
        food_preference = _extract_food_preference(context.profile.preferences)
        if food_preference:
            light_memory = f"要是想到{food_preference}，我们就先从那个开始。"
    if not light_memory:
        light_memory = _pick_one(
            conversation_phrases.CURRENT_NEED_LIGHT_MEMORY.get(need, ()),
            context.recent_logs,
            last_reply=context.last_reply,
            fallback="",
        )

    parts = [opening, follow]
    if light_memory:
        parts.append(light_memory)
    return "".join(parts)


def _build_comment_reply(context: ConversationContext) -> str:
    """Respond to short evaluative comments without jumping into memory guidance."""
    if context.user_message.strip() in {"是吗", "对", "是啊", "嗯对"} and context.last_reply:
        clarification_prefix = _pick_one(
            conversation_phrases.CLARIFICATION_DIRECT_PREFIXES,
            context.recent_logs,
            last_reply=context.last_reply,
            fallback="我刚刚说的是",
        )
        return f"{clarification_prefix}{_summarize_last_reply(context.last_reply)}。"

    opening = _pick_one(
        conversation_phrases.COMMENT_ACKNOWLEDGEMENTS,
        context.recent_logs,
        last_reply=context.last_reply,
        fallback="对，",
    )
    response = _pick_one(
        conversation_phrases.COMMENT_RESPONSES,
        context.recent_logs,
        last_reply=context.last_reply,
        fallback="这样一说，确实挺像样的。",
    )
    return f"{opening}{response}"


def _build_direct_fact_reply(context: ConversationContext) -> str | None:
    """Answer direct identity or profile questions without sounding robotic."""
    message = context.user_message
    profile = context.profile

    if "我是谁" in message or "我的名字" in message or "我叫什么" in message:
        if profile.name:
            opening = _pick_one(
                conversation_phrases.DIRECT_IDENTITY_OPENINGS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            follow = _pick_one(
                conversation_phrases.DIRECT_IDENTITY_FOLLOWS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            return f"{opening}{profile.name}。{follow}"
        return conversation_phrases.DIRECT_IDENTITY_FALLBACK

    if "我多大" in message or "年龄" in message:
        if profile.age is not None:
            opening = _pick_one(
                conversation_phrases.DIRECT_AGE_OPENINGS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            follow = _pick_one(
                conversation_phrases.DIRECT_AGE_FOLLOWS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            return f"{opening}{profile.age}岁。{follow}"
        return conversation_phrases.DIRECT_AGE_FALLBACK

    if "家乡" in message or "哪里人" in message:
        hometown = _trim(profile.hometown)
        if hometown:
            opening = _pick_one(
                conversation_phrases.DIRECT_HOMETOWN_OPENINGS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            follow = _pick_one(
                conversation_phrases.DIRECT_HOMETOWN_FOLLOWS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            return f"{opening}{hometown}。{follow}"
        return conversation_phrases.DIRECT_HOMETOWN_FALLBACK

    if any(key in message for key in FAMILY_HINTS):
        family = _trim(profile.family_info)
        if family:
            relation = ""
            for candidate in ("女儿", "儿子", "妈妈", "爸爸", "老伴", "丈夫", "爱人"):
                if candidate in message:
                    relation = candidate
                    break
            relation_snippet = _extract_relation_snippet(family, relation) if relation else ""
            focus = relation_snippet or family
            opening = _pick_one(
                conversation_phrases.DIRECT_FAMILY_OPENINGS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            follow = _pick_one(
                conversation_phrases.DIRECT_FAMILY_FOLLOWS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            return f"{opening}{focus}。{follow}"
        return conversation_phrases.DIRECT_FAMILY_FALLBACK

    if any(key in message for key in LIFE_HINTS):
        life = _trim(profile.life_events)
        if life:
            opening = _pick_one(
                conversation_phrases.DIRECT_LIFE_OPENINGS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            follow = _pick_one(
                conversation_phrases.DIRECT_LIFE_FOLLOWS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            return f"{opening}{life}。{follow}"
        return conversation_phrases.DIRECT_LIFE_FALLBACK

    if any(key in message for key in PREFERENCE_HINTS):
        preference = _trim(profile.preferences)
        if preference:
            opening = _pick_one(
                conversation_phrases.DIRECT_PREFERENCE_OPENINGS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            follow = _pick_one(
                conversation_phrases.DIRECT_PREFERENCE_FOLLOWS,
                context.recent_logs,
                last_reply=context.last_reply,
            )
            return f"{opening}{preference}。{follow}"
        return conversation_phrases.DIRECT_PREFERENCE_FALLBACK

    return None


def _build_opening(strategy: Strategy, context: ConversationContext) -> str:
    """Build the first natural sentence while respecting soft cooldown."""
    avoid_soft = _soft_cooldown_active(context.recent_logs)
    state = context.state

    options: list[str]
    if strategy == "complaint_repair":
        options = list(conversation_phrases.COMPLAINT_OPENINGS)
    elif strategy == "clarification_repair":
        options = list(conversation_phrases.CLARIFICATION_OPENINGS)
    elif strategy == "current_need_response":
        options = list(
            conversation_phrases.CURRENT_NEED_OPENINGS.get(
                context.state.current_need or "discomfort",
                (),
            )
        )
    elif strategy == "repeat_soft_response":
        options = list(conversation_phrases.REPEAT_OPENINGS)
    elif strategy == "light_support":
        if state.short_input_kind == "forgetful":
            options = list(conversation_phrases.LIGHT_SUPPORT_OPENINGS["forgetful"])
        elif state.short_input_kind == "uncertain":
            options = list(conversation_phrases.LIGHT_SUPPORT_OPENINGS["uncertain"])
        else:
            options = list(conversation_phrases.LIGHT_SUPPORT_OPENINGS["brief_ack"])
    elif strategy == "familiar_guidance":
        if state.short_input_kind == "forgetful":
            options = list(conversation_phrases.LIGHT_SUPPORT_OPENINGS["forgetful"])
        elif state.short_input_kind == "uncertain":
            options = list(conversation_phrases.LIGHT_SUPPORT_OPENINGS["uncertain"])
        else:
            options = list(conversation_phrases.LIGHT_SUPPORT_OPENINGS["familiar"])
    else:
        options = list(conversation_phrases.OPENINGS)

    return _pick_one(
        options,
        context.recent_logs,
        last_reply=context.last_reply,
        avoid_soft=avoid_soft,
        fallback="好。",
    )


def _build_guidance_sentence(topic: Topic, anchor_text: str, context: ConversationContext) -> str:
    """Build one gentle follow-up line around the current familiar anchor."""
    if topic == "family" and anchor_text:
        return _pick_one(
            [_format_phrase(template, anchor=anchor_text) for template in conversation_phrases.FAMILY_GUIDANCE],
            context.recent_logs,
            last_reply=context.last_reply,
        )

    if topic == "life" and anchor_text:
        return _pick_one(
            [_format_phrase(template, anchor=anchor_text) for template in conversation_phrases.LIFE_GUIDANCE],
            context.recent_logs,
            last_reply=context.last_reply,
        )

    if topic == "preference" and anchor_text:
        return _pick_one(
            [_format_phrase(template, anchor=anchor_text) for template in conversation_phrases.PREFERENCE_GUIDANCE],
            context.recent_logs,
            last_reply=context.last_reply,
        )

    if topic == "place" and anchor_text:
        return _pick_one(
            [_format_phrase(template, anchor=anchor_text) for template in conversation_phrases.HOMETOWN_GUIDANCE],
            context.recent_logs,
            last_reply=context.last_reply,
        )

    if anchor_text:
        return _pick_one(
            [_format_phrase(template, anchor=anchor_text) for template in conversation_phrases.GENERAL_GUIDANCE],
            context.recent_logs,
            last_reply=context.last_reply,
        )

    return _pick_one(
        conversation_phrases.GENERAL_GUIDANCE,
        context.recent_logs,
        last_reply=context.last_reply,
    )


def _build_tail(strategy: Strategy, context: ConversationContext) -> str:
    """Optionally add one light closing sentence without forcing the user."""
    if strategy == "repeat_soft_response":
        options = list(conversation_phrases.SOFT_ENDINGS["repeat"])
    elif strategy == "complaint_repair":
        options = list(conversation_phrases.SOFT_ENDINGS["complaint"])
    elif strategy in {"clarification_repair", "current_need_response"}:
        options = [""]
    else:
        options = list(conversation_phrases.SOFT_ENDINGS["default"])

    return _pick_one(options, context.recent_logs, last_reply=context.last_reply, fallback="")


def _build_repeat_repair(context: ConversationContext) -> str:
    """Change course when the dialogue is getting stuck in the same wording."""
    opening = _pick_one(
        conversation_phrases.REPEAT_REPAIRS,
        context.recent_logs,
        last_reply=context.last_reply,
        fallback="我换个说法接你这句。",
    )
    if context.state.current_need is not None:
        return f"{opening}{_build_current_need_reply(context)}"
    if context.state.clarification_request:
        return f"{opening}{_build_clarification_reply(context)}"
    recovery = _pick_one(
        conversation_phrases.GENERAL_RECOVERY,
        context.recent_logs,
        last_reply=context.last_reply,
        fallback="你先说现在最想接的一句，我跟着你。",
    )
    return f"{opening}{recovery}"


def _is_reply_too_similar(candidate: str, recent_logs: Sequence[ChatLog]) -> bool:
    """Block near-duplicate assistant replies when the last turns are already stuck."""
    assistant_messages = _recent_assistant_messages(recent_logs, limit=2)
    if not assistant_messages:
        return False
    if _assistant_reply_similarity(candidate, assistant_messages[-1]) >= 0.86:
        return True
    if len(assistant_messages) >= 2 and _assistant_reply_similarity(candidate, assistant_messages[-2]) >= 0.9:
        return True
    return False


def _build_care_scenario_reply(context: ConversationContext) -> str | None:
    """Return deterministic short replies for high-risk care scenes."""
    scenario = context.state.care_scenario
    message = context.user_message

    if scenario in {"medication_confusion", "medication_uncertainty"}:
        return "我先不乱说你吃没吃。我们一起请小雨确认一下，好吗？你先坐稳，别着急。"

    if scenario in {"fear_anxiety", "anxiety_abandonment"}:
        return "李奶奶，你不是一个人。我在这里陪你。小雨也一直惦记着你。"

    if scenario in {"going_home", "disorientation_going_home"}:
        return "李奶奶，你现在是安全的。我陪你慢慢确认一下。我们先坐一会儿，再请小雨联系你，好吗？"

    if scenario in {"wandering_risk", "wandering_intent"}:
        return "李奶奶，先别一个人出去。外面可能不太安全。我们先联系小雨，再一起决定，好吗？"

    if scenario == "repeated_question_xiaoyu":
        return "李奶奶，小雨晚上 8 点左右会联系你。她一直惦记着你。我们先安心坐一会儿，好吗？"

    if scenario == "self_awareness_repeated_question":
        return "没关系，李奶奶。你想问什么，我都可以再陪你说一遍。"

    if scenario == "repeated_question":
        return "这件事我陪你再确认一遍。我们可以请家人留个提醒卡片，放在容易看到的地方。"

    if scenario == "person_recognition":
        return "我现在还看不到照片。我们可以请小雨帮你确认一下。"

    if scenario in {"sensitive_deceased_spouse_topic", "deceased_spouse_sensitive"}:
        return "你有点想老王了。我们先坐一会儿，我陪你听一首熟悉的老歌，好吗？"

    if scenario == "date_time_confusion":
        return "今天的日期我可以慢慢告诉你。我们先看一下时间，不着急。"

    if scenario == "suspicion_or_delusion":
        return "听起来你有点担心。我们先一起看一下常放的位置，也可以请小雨帮忙确认。"

    return None


def generate_reply(strategy: Strategy, context: ConversationContext) -> str:
    """Generate a lightweight local fallback reply.

    This function is no longer the main expression layer. It only provides a
    concise mock fallback when the real model is unavailable.
    """
    care_reply = _build_care_scenario_reply(context)
    if care_reply:
        return care_reply

    direct_fact_reply = _build_direct_fact_reply(context)
    if strategy == "clarification_repair":
        candidate = _build_clarification_reply(context)
        return candidate if not _is_reply_too_similar(candidate, context.recent_logs) else _build_repeat_repair(context)

    if strategy == "current_need_response":
        candidate = _build_current_need_reply(context)
        return candidate if not _is_reply_too_similar(candidate, context.recent_logs) else _build_repeat_repair(context)

    if context.state.input_kind == "comment":
        candidate = _build_comment_reply(context)
        return candidate if not _is_reply_too_similar(candidate, context.recent_logs) else "对，听起来确实是这样。"

    if direct_fact_reply and strategy != "complaint_repair":
        return direct_fact_reply if not _is_reply_too_similar(direct_fact_reply, context.recent_logs) else _build_repeat_repair(context)

    if strategy == "complaint_repair":
        candidate = _pick_one(
            conversation_phrases.COMPLAINT_REPAIRS,
            context.recent_logs,
            last_reply=context.last_reply,
            fallback="那我们不绕，先说你现在最在意的这件事。",
        )
        return candidate if not _is_reply_too_similar(candidate, context.recent_logs) else _build_repeat_repair(context)

    if strategy == "repeat_soft_response":
        return _build_repeat_repair(context)

    if not context.state.memory_guidance_active:
        candidate = _pick_one(
            conversation_phrases.GENERAL_RECOVERY,
            context.recent_logs,
            last_reply=context.last_reply,
            fallback="你接着说，我跟着你。",
        )
        return candidate if not _is_reply_too_similar(candidate, context.recent_logs) else "你接着说，我在听。"

    topic, anchor_text = _build_anchor(context.state.current_topic, context)
    if topic != "general" and anchor_text:
        candidate = _build_guidance_sentence(topic, anchor_text, context)
    elif anchor_text:
        candidate = _build_guidance_sentence("general", anchor_text, context)
    elif context.state.short_input:
        candidate = _pick_one(
            conversation_phrases.GENERAL_RECOVERY,
            context.recent_logs,
            last_reply=context.last_reply,
            fallback="你先说现在最想接的一句，我跟着你。",
        )
    else:
        candidate = _pick_one(
            conversation_phrases.OPENINGS,
            context.recent_logs,
            last_reply=context.last_reply,
            fallback="好。",
        )

    if _recent_assistant_repetition_active(context.recent_logs) or _is_reply_too_similar(candidate, context.recent_logs):
        return _build_repeat_repair(context)
    return candidate
