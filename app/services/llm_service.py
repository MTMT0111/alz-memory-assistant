"""Provider-switchable LLM service layer with safe mock fallback.

This module keeps all model access in one place:
- provider selection and credential resolution
- OpenAI-compatible client calls for multiple providers
- response guards and relevance checks
- mock fallback for missing keys, SDK issues, or bad remote output

The rest of the app should not need to care which provider is active.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import os
import re
from typing import Any, Protocol, Sequence

from app.config import load_local_env_file
from app.models.chat_log import ChatLog
from app.models.user_profile import UserProfile
from app.services import conversation_style_engine

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in local setups
    OpenAI = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)

load_local_env_file()

# Configuration defaults
DEFAULT_PROVIDER = "deepseek"
DEFAULT_PROVIDER_BASE_URLS = {
    "zhipu": "https://open.bigmodel.cn/api/paas/v4/",
    "deepseek": "https://api.deepseek.com/v1",
    "minimax": "https://api.minimax.io/v1",
    "openai": "https://api.openai.com/v1",
}
DEFAULT_PROVIDER_MODELS = {
    "zhipu": "glm-4",
    "deepseek": "deepseek-v4-flash",
    "minimax": "MiniMax-M2.7",
    "openai": "gpt-4o-mini",
}

# Output and timeout settings (configurable via environment variables)
MAX_REPLY_CHARS = int(os.getenv("LLM_MAX_OUTPUT_CHARS", "160"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
LLM_ENABLE_FALLBACK = os.getenv("LLM_ENABLE_FALLBACK", "true").strip().lower() not in {"0", "false", "no", "off"}
_LLM_CONFIG_LOGGED = False

META_REPLY_MARKERS = (
    "根据你提供的资料",
    "根据上述信息",
    "根据最近聊天记录",
    "根据你的输入",
    "我会顺着这些线索",
    "当前陪伴场景",
    "系统提示",
    "当前策略",
    "上下文",
    "内部",
    "作为一个ai",
    "作为一个 AI",
    "我正在分析",
)

SCRIPTED_REPLY_MARKERS = (
    "先从",
    "说起吧",
    "一提起来",
    "后面的事就",
    "后面的事也许就",
    "也许就",
    "让你慢慢想起来",
)

FIELD_STYLE_MARKERS = (
    "女儿：",
    "儿子：",
    "丈夫：",
    "妈妈：",
    "爸爸：",
    "喜欢：",
    "家乡：",
)

SOFT_FILTER_MARKERS = (
    "没关系",
    "慢慢来",
    "不着急",
    "别着急",
)

TESTING_MARKERS = (
    "你还记得吗",
    "还记得吗",
    "记不记得",
    "你记得吗",
)

RESTRICTED_CARE_MARKERS = (
    "你忘了",
    "你记错了",
    "你已经问过了",
    "你怎么又问",
    "你不正常",
    "你必须",
    "不要胡思乱想",
    "没救",
    "严重恶化",
    "诊断为",
    "得了阿尔兹海默症",
    "你有阿尔兹海默症",
    "已经去世",
    "去世了",
    "治疗方案",
)


@dataclass(slots=True)
class LLMConversationInput:
    """Structured conversation payload passed into the reply generator."""

    system_prompt: str
    support_mode: str
    profile: UserProfile
    recent_logs: Sequence[ChatLog]
    user_message: str
    context_text: str
    memory_summary: str = ""
    last_reply: str = ""
    style_state: conversation_style_engine.ConversationState | None = None
    style_strategy: conversation_style_engine.Strategy | None = None


@dataclass(slots=True)
class ResolvedStyleContext:
    """Resolved state shared by both mock and real LLM paths."""

    state: conversation_style_engine.ConversationState
    strategy: conversation_style_engine.Strategy
    context: conversation_style_engine.ConversationContext


@dataclass(slots=True)
class ProviderConfig:
    """Resolved runtime configuration for one LLM provider."""

    provider: str
    api_key: str = ""
    base_url: str = ""
    model: str = ""


@dataclass(slots=True)
class ProviderAvailability:
    """Human-readable availability state for one provider."""

    provider: str
    available: bool
    reason: str
    model: str
    base_url: str


@dataclass(slots=True)
class LLMReplyResult:
    """Reply plus debug metadata for evals and lightweight observability."""

    reply: str
    requested_provider: str
    actual_provider: str
    model: str
    fallback_used: bool
    fallback_reason: str = ""
    guard_triggered: bool = False
    guard_reason: str = ""
    raw_llm_reply: str = ""
    postprocess_used: bool = False
    safe_template_reply: str = ""
    template_used: bool = False
    template_name: str = ""


class LLMService(Protocol):
    """Small protocol so future provider implementations can swap in cleanly."""

    def generate_reply(self, conversation: LLMConversationInput) -> str:  # type: ignore
        """Return the assistant's next reply."""

    def generate_reply_result(self, conversation: LLMConversationInput) -> LLMReplyResult:  # type: ignore
        """Return the reply plus provider metadata."""


def _resolve_style_context(conversation: LLMConversationInput) -> ResolvedStyleContext:
    """Resolve state, strategy, and style-engine context in one place."""
    state = conversation.style_state or conversation_style_engine.detect_user_state(
        conversation.user_message,
        conversation.recent_logs,
    )
    strategy = conversation.style_strategy or conversation_style_engine.decide_strategy(state)
    context = conversation_style_engine.ConversationContext(
        profile=conversation.profile,
        recent_logs=conversation.recent_logs,
        user_message=conversation.user_message,
        state=state,
        last_reply=conversation.last_reply,
    )
    return ResolvedStyleContext(state=state, strategy=strategy, context=context)


def _build_mock_reply(conversation: LLMConversationInput) -> str:
    """Generate the local fallback reply through the style engine."""
    resolved = _resolve_style_context(conversation)
    return conversation_style_engine.generate_reply(resolved.strategy, resolved.context)


def _clean_profile_value(value: str) -> str:
    """Normalize stored profile text before it reaches the model."""
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    cleaned = cleaned.replace("；", "，").replace("。", "，")
    cleaned = re.sub(r"(什么会让ta更愿意继续说下去|哪些日子和片段最熟悉|扎辫子的小女孩)", "", cleaned)
    cleaned = re.sub(r"一提起来.*", "", cleaned)
    cleaned = re.sub(r"，{2,}", "，", cleaned).strip("， ")
    return cleaned


def _profile_text(profile: UserProfile) -> str:
    """Turn the profile into short factual lines without script-like phrasing."""
    lines: list[str] = []

    base_parts: list[str] = []
    if profile.name:
        base_parts.append(profile.name)
    if profile.age is not None:
        base_parts.append(f"{profile.age}岁左右")
    if profile.hometown:
        base_parts.append(f"熟悉{_clean_profile_value(profile.hometown)}")
    if base_parts:
        lines.append("基本信息：" + "，".join(base_parts))

    family_text = _clean_profile_value(profile.family_info)
    life_text = _clean_profile_value(profile.life_events)
    preference_text = _clean_profile_value(profile.preferences)
    notes_text = _clean_profile_value(profile.notes)

    if family_text:
        lines.append(f"重要家人：{family_text}")
    if life_text:
        lines.append(f"熟悉经历：{life_text}")
    if preference_text:
        lines.append(f"喜好：{preference_text}")
    if notes_text:
        lines.append(f"陪伴提醒：{notes_text}")

    return "\n".join(lines[:5]) if lines else "暂无资料。"


def _history_text(logs: Sequence[ChatLog]) -> str:
    """Convert only a few recent turns into a compact context block."""
    if not logs:
        return "暂无最近对话。"

    lines: list[str] = []
    recent_logs = list(logs[-4:])

    for log in recent_logs:
        speaker = "用户" if log.role == "user" else "助手"
        message = str(log.message or "").strip()
        if not message:
            continue
        lines.append(f"{speaker}：{message}")

    return "\n".join(lines) if lines else "暂无最近对话。"


def _memory_summary_text(summary: str) -> str:
    """Keep only a few factual long-term summary lines."""
    raw_lines = [
        line.strip(" -")
        for line in re.split(r"[。\n]", str(summary or ""))
        if line.strip(" -")
    ]
    compact_lines: list[str] = []
    for line in raw_lines:
        cleaned = re.sub(r"\s+", " ", line).strip()
        if not cleaned:
            continue
        cleaned = (
            cleaned.replace("常提到的人有", "常提到：")
            .replace("常聊经历有", "常聊经历：")
            .replace("偏好线索里有", "常见喜好：")
            .replace("熟悉地点会回到", "熟悉地点：")
            .replace("重复会回到", "容易重复：")
        )
        cleaned = re.sub(r"一提起来.*", "", cleaned).strip("， ")
        compact_lines.append(cleaned[:36])
        if len(compact_lines) >= 4:
            break

    if not compact_lines:
        return "暂无稳定的长期记忆摘要。"

    return "\n".join(f"- {line}" for line in compact_lines)


def _build_state_tags(resolved: ResolvedStyleContext) -> list[str]:
    """Convert the lightweight state detection into prompt-friendly labels."""
    state = resolved.state
    tags: list[str] = [f"input_kind:{state.input_kind}"]

    if state.short_input:
        tags.append(f"short_input:{state.short_input_kind or 'yes'}")
    if state.repeat_question:
        tags.append("repeat_question")
    if state.clarification_request:
        tags.append("clarification")
    if state.current_need:
        tags.append(f"current_need:{state.current_need}")
    if state.memory_question:
        tags.append("memory_question")
    if state.confusion:
        tags.append("confusion")
    if state.emotional:
        tags.append("emotional")
    if state.complaint_tone:
        tags.append("complaint")
    if state.family_topic:
        tags.append("family_topic")
    if state.life_topic:
        tags.append("life_topic")
    if state.preference_topic:
        tags.append("preference_topic")
    if state.place_topic:
        tags.append("place_topic")
    if getattr(state, "care_scenario", "general") != "general":
        tags.append(f"care_scenario:{state.care_scenario}")
    tags.append(f"current_topic:{state.current_topic}")
    return tags


def _build_real_system_prompt(
    conversation: LLMConversationInput,
    resolved: ResolvedStyleContext,
) -> str:
    """Build a short system prompt with only the key companion boundaries."""
    state_tags = _build_state_tags(resolved)
    return "\n".join(
        [
            "你在和一位可能存在记忆困扰的老人聊天。",
            "请像熟人一样自然接话，先回应当前这句话，再决定是否参考资料。",
            "不要解释系统过程，不要纠错，不要争辩，不要测试记忆。",
            "不要把后台资料、字段标题或人物设定直接念给用户听。",
            "clarification、comment 和当前需求类输入优先短答，不要切去别的话题。",
            "资料和记忆摘要只是辅助，不要压过当前输入。",
            "不要写得像引导稿、旁白或咨询脚本。",
            "遇到吃药不确定：不要判断吃没吃过，先说一起确认提醒或药盒，并建议请家人核对。",
            "遇到害怕、想回家、位置困惑、外出意图、怀疑被偷：先安抚，再确认安全或联系家人；不要反驳或争辩。",
            "遇到人物识别困难：不要考记忆，不确定就说明一起看照片或请家人确认。",
            "Demo 患者规则：你正在和 78 岁的李桂兰（李奶奶）说话。",
            "她常问女儿小雨什么时候回来；小雨晚上 8 点左右会联系她。",
            "不要说“作为AI模型”，不要说“你刚刚问过”，不要说“你忘了”。",
            "遇到“我要回家/这里是哪里/想出去”：先安抚，再提醒联系小雨或在安全地方等一下。",
            "遇到“老王怎么还没回来”：不要说老王已经去世；说“你有点想老王了。我们先坐一会儿，我陪你听一首熟悉的老歌，好吗？”",
            "遇到吃药不确定：不要说已吃或没吃；说一起请小雨确认。",
            "遇到“这个人是谁”：没有图片上下文就不要编造，说现在看不到照片，可以请小雨确认。",
            "遇到“我刚刚是不是问过你”：说没关系，可以再陪她说一遍。",
            "输出中文，通常 1 到 3 句，简短、自然、有陪伴感。",
            conversation.system_prompt.strip(),
            f"状态标签：{', '.join(state_tags)}",
        ]
    )


def _build_real_llm_messages(
    conversation: LLMConversationInput,
    resolved: ResolvedStyleContext,
) -> list[dict[str, str]]:
    """Build compatible messages with the current user input as the true user turn."""
    runtime_style_prompt = _build_real_system_prompt(conversation, resolved)
    user_payload = "\n\n".join(
        [
            "请参考下面这些辅助资料，自然回复。资料只在合适时参考，不要直接复述字段。",
            "【这个人的简短情况】",
            _profile_text(conversation.profile),
            "【可参考的长期线索】",
            _memory_summary_text(conversation.memory_summary),
            "【最近几句对话】",
            _history_text(conversation.recent_logs),
            "【当前用户消息｜优先回应这一句】",
            conversation.user_message.strip(),
        ]
    )
    return [
        {"role": "system", "content": runtime_style_prompt},
        {"role": "user", "content": user_payload},
    ]


def _extract_response_text(response: Any) -> str:
    """Extract the first text response from an OpenAI-compatible SDK result."""
    try:
        choice = response.choices[0]
        message = getattr(choice, "message", None)
        content = getattr(message, "content", "")
    except Exception:
        return ""

    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    parts.append(text)
            else:
                text = getattr(item, "text", "")
                if text:
                    parts.append(str(text).strip())
        return "\n".join(part for part in parts if part).strip()
    return str(content or "").strip()


def _looks_like_meta_reply(text: str) -> bool:
    """Filter out responses that expose system/process language to the user."""
    if not text:
        return True
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in META_REPLY_MARKERS)


def _looks_like_scripted_reply(text: str) -> bool:
    """Detect obvious script-like companion wording."""
    return any(marker in text for marker in SCRIPTED_REPLY_MARKERS)


def _looks_like_field_style_reply(text: str) -> bool:
    """Detect output that looks like leaked backend fields."""
    return any(marker in text for marker in FIELD_STYLE_MARKERS)


def _normalize_reply_text(text: str) -> str:
    """Collapse extra whitespace before running reply guards."""
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    return compact.replace("。。", "。")


def _split_sentences(text: str) -> list[str]:
    """Split Chinese text into lightweight sentence units."""
    pieces = re.split(r"(?<=[。！？!?])\s*", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def _clean_meta_sentences(text: str) -> str:
    """Remove obviously meta or system-explaining sentences when possible."""
    kept = [
        sentence
        for sentence in _split_sentences(text)
        if not _looks_like_meta_reply(sentence)
        and not _looks_like_scripted_reply(sentence)
        and not _looks_like_field_style_reply(sentence)
    ]
    return "".join(kept).strip()


def _clean_field_style_reply(text: str) -> str:
    """Strip field-like labels when they slip into the output."""
    cleaned = str(text or "")
    for marker in FIELD_STYLE_MARKERS:
        cleaned = cleaned.replace(marker, "")
    return re.sub(r"\s+", " ", cleaned).strip()


def _too_much_soft_reassurance(text: str) -> bool:
    """Detect over-dense reassurance wording so replies stay natural."""
    count = sum(text.count(marker) for marker in SOFT_FILTER_MARKERS)
    return count >= 2


def _looks_like_memory_test(text: str) -> bool:
    """Avoid replies that sound like testing the user's memory."""
    return any(marker in text for marker in TESTING_MARKERS)


def _contains_restricted_care_marker(text: str) -> bool:
    """Avoid wording that can shame, frighten, or over-medicalize the patient."""
    return any(marker in text for marker in RESTRICTED_CARE_MARKERS)


def _truncate_reply(text: str) -> str:
    """Keep replies short and readable for this companion setting."""
    sentences = _split_sentences(text)
    if not sentences:
        return ""

    collected: list[str] = []
    total = 0
    for sentence in sentences:
        next_total = total + len(sentence)
        if collected and (len(collected) >= 3 or next_total > MAX_REPLY_CHARS):
            break
        collected.append(sentence)
        total = next_total

    reply = "".join(collected).strip()
    if len(reply) > MAX_REPLY_CHARS:
        reply = reply[:MAX_REPLY_CHARS].rstrip("，,；;：: ")
        if reply and reply[-1] not in "。！？!?":
            reply += "。"
    return reply


def _is_too_similar_to_recent_assistant(reply: str, recent_logs: Sequence[ChatLog]) -> bool:
    """Block obvious near-duplicate assistant outputs."""
    if not reply:
        return True
    recent_assistant = [log.message for log in recent_logs if log.role == "assistant"][-2:]
    normalized_reply = conversation_style_engine._normalize_text(reply)
    if not normalized_reply:
        return True
    for previous in recent_assistant:
        similarity = conversation_style_engine._assistant_reply_similarity(reply, previous)
        if similarity >= 0.88:
            return True
    return False


def _extract_relation_snippet(family_info: str, relation: str) -> str:
    """Extract one short family snippet for direct relation questions."""
    if not family_info or not relation:
        return ""
    pattern = re.compile(rf"({relation}[^，。；;\n]*)")
    match = pattern.search(family_info)
    return match.group(1).strip() if match else ""


def _reply_matches_need(reply: str, need: str) -> bool:
    """Check whether the reply is at least roughly aligned with an immediate need."""
    hint_map = {
        "hungry": ("吃", "喝", "粥", "面", "饭", "点心", "饿"),
        "food": ("吃", "喝", "粥", "面", "饭", "点心"),
        "tired": ("歇", "休息", "坐", "靠", "缓", "累"),
        "sleepy": ("睡", "歇", "困", "躺", "休息"),
        "discomfort": ("舒服", "难受", "缓", "喝水", "哪里", "不舒服"),
    }
    return any(token in reply for token in hint_map.get(need, ()))


def _reply_matches_clarification(reply: str, last_reply: str) -> bool:
    """Check whether a clarification reply stays near the last assistant turn."""
    if any(marker in reply for marker in ("刚刚", "我是说", "那句", "意思是")):
        return True
    last_pieces = [
        piece.strip() for piece in re.split(r"[，,。！？!?；;\n]", str(last_reply or ""))
        if piece.strip() and len(piece.strip()) >= 2
    ]
    return any(piece in reply for piece in last_pieces[:3])


def _fails_direct_question_guard(conversation: LLMConversationInput, reply: str) -> bool:
    """Keep direct profile questions from drifting into unrelated answers."""
    message = conversation.user_message
    profile = conversation.profile
    normalized_reply = conversation_style_engine._normalize_text(reply)

    if not normalized_reply:
        return True

    if ("我是谁" in message or "我的名字" in message or "我叫什么" in message) and profile.name:
        if conversation_style_engine._normalize_text(profile.name) not in normalized_reply:
            return True
        if "我是" in reply and "你是" not in reply:
            return True

    for relation in ("女儿", "儿子", "妈妈", "爸爸", "老伴", "丈夫", "爱人"):
        if relation in message and "谁" in message and profile.family_info:
            snippet = _extract_relation_snippet(profile.family_info, relation)
            if not snippet:
                return False
            snippet_normalized = conversation_style_engine._normalize_text(snippet)
            return snippet_normalized not in normalized_reply and conversation_style_engine._normalize_text(relation) not in normalized_reply

    if ("我多大" in message or "年龄" in message) and profile.age is not None:
        return str(profile.age) not in reply

    if ("家乡" in message or "哪里人" in message) and profile.hometown:
        return conversation_style_engine._normalize_text(profile.hometown) not in normalized_reply

    return False


def _fails_relevance_guard(
    conversation: LLMConversationInput,
    resolved: ResolvedStyleContext,
    reply: str,
) -> bool:
    """Reject replies that are clearly misaligned with the current user input."""
    state = resolved.state

    if state.current_need and not _reply_matches_need(reply, state.current_need):
        return True

    if state.clarification_request and not _reply_matches_clarification(reply, conversation.last_reply):
        return True
    if state.clarification_request and any(token in reply for token in ("女儿", "儿子", "丈夫", "家乡")) and "刚刚" not in reply:
        return True

    if state.memory_question and _fails_direct_question_guard(conversation, reply):
        return True

    if state.input_kind == "comment" and (
        "？" in reply
        or "?" in reply
        or _looks_like_scripted_reply(reply)
        or _looks_like_field_style_reply(reply)
    ):
        return True

    if state.confusion and not any(token in reply for token in ("这里", "现在", "你先", "我陪着", "在这")):
        return True

    care_scenario = getattr(state, "care_scenario", "general")
    if care_scenario in {"medication_confusion", "medication_uncertainty"}:
        return not any(token in reply for token in ("确认", "药盒", "提醒", "家人", "小雨", "看一下"))
    if care_scenario in {"fear_anxiety", "anxiety_abandonment"}:
        return not any(token in reply for token in ("我在", "我陪", "安全", "坐一会", "联系", "小雨", "家人"))
    if care_scenario in {"going_home", "disorientation_going_home"}:
        if any(
            token in reply
            for token in (
                "这里就是你的家",
                "这里就是您家",
                "这里是你家",
                "这里是您家",
                "这儿就是你的家",
                "这儿就是您家",
                "这是你家",
                "这是您家",
                "这就是你的家",
                "这就是您家",
                "这里就是家里",
                "现在就在家里",
                "你现在在家",
                "您现在在家",
                "你就在自己家里",
                "您就在自己家里",
                "就在自己家里",
                "就在你家",
                "就在您家",
            )
        ):
            return True
        return not any(token in reply for token in ("哪里", "位置", "安全", "联系", "确认", "小雨", "家人"))
    if care_scenario in {"wandering_risk", "wandering_intent"}:
        if any(token in reply for token in ("自己出去", "一个人出去", "现在就出去")):
            return True
        return not any(token in reply for token in ("陪", "家人", "小雨", "安全", "先等等", "不要一个人"))
    if care_scenario == "repeated_question_xiaoyu":
        return not ("小雨" in reply and any(token in reply for token in ("晚上", "8点", "8 点", "联系", "惦记")))
    if care_scenario == "self_awareness_repeated_question":
        return not any(token in reply for token in ("没关系", "陪你", "再陪", "再说", "慢慢"))
    if care_scenario == "person_recognition":
        if any(token in reply for token in ("你不记得", "记不记得", "你忘了")):
            return True
        return not any(token in reply for token in ("照片", "确认", "小雨", "家人", "我这里"))
    if care_scenario == "suspicion_or_delusion":
        if any(token in reply for token in ("没人偷", "你想多了", "不要胡思乱想")):
            return True
        return not any(token in reply for token in ("担心", "一起", "看一下", "确认", "小雨", "家人"))
    if care_scenario in {"sensitive_deceased_spouse_topic", "deceased_spouse_sensitive"}:
        if any(token in reply for token in ("在外面", "忙着", "上班", "工作", "等他", "会回来", "快回来了")):
            return True
        return not any(token in reply for token in ("想他", "想念", "坐一会", "老歌", "我陪", "陪你"))
    if care_scenario == "date_time_confusion":
        if "今天" in reply and any(token in reply for token in ("日", "号", "星期", "点")):
            now = datetime.now()
            accepted_dates = {
                now.strftime("%Y年%m月%d日"),
                f"{now.year}年{now.month}月{now.day}日",
                f"{now.month}月{now.day}日",
                f"{now.month}月{now.day}号",
            }
            return not any(date_text and date_text in reply for date_text in accepted_dates)
        return not any(token in reply for token in ("日期", "时间", "看一下", "日历", "慢慢"))

    if state.input_kind == "short_input" and state.current_topic != "general":
        return False

    return False


def _guard_real_reply(reply: str, mock_reference: str, recent_logs: Sequence[ChatLog]) -> str:
    """Clean and validate real-model output before returning it to the user."""
    cleaned = _normalize_reply_text(reply)
    if not cleaned:
        return mock_reference

    cleaned = _clean_meta_sentences(cleaned)
    cleaned = _clean_field_style_reply(cleaned)
    cleaned = _normalize_reply_text(cleaned)
    if not cleaned:
        return mock_reference
    if _looks_like_meta_reply(cleaned):
        return mock_reference
    if _looks_like_scripted_reply(cleaned):
        return mock_reference
    if _looks_like_field_style_reply(cleaned):
        return mock_reference
    if _too_much_soft_reassurance(cleaned):
        return mock_reference
    if _looks_like_memory_test(cleaned):
        return mock_reference
    if _contains_restricted_care_marker(cleaned):
        return mock_reference
    if _is_too_similar_to_recent_assistant(cleaned, recent_logs):
        return mock_reference

    shortened = _truncate_reply(cleaned)
    if not shortened:
        return mock_reference
    if _looks_like_meta_reply(shortened):
        return mock_reference
    if _looks_like_scripted_reply(shortened):
        return mock_reference
    if _looks_like_field_style_reply(shortened):
        return mock_reference
    if _too_much_soft_reassurance(shortened):
        return mock_reference
    if _looks_like_memory_test(shortened):
        return mock_reference
    if _contains_restricted_care_marker(shortened):
        return mock_reference
    if _is_too_similar_to_recent_assistant(shortened, recent_logs):
        return mock_reference
    return shortened


def _classify_response_guard_issue(reply: str, recent_logs: Sequence[ChatLog]) -> str:
    """Explain which response-guard family most likely rejected the raw reply."""
    cleaned = _normalize_reply_text(reply)
    if not cleaned:
        return "response_guard_triggered"
    if _looks_like_meta_reply(cleaned):
        return "system_like_response_guard"
    if _looks_like_field_style_reply(cleaned):
        return "field_leakage_guard"
    if _looks_like_scripted_reply(cleaned):
        return "scripted_guidance_guard"
    if _too_much_soft_reassurance(cleaned) or _looks_like_memory_test(cleaned):
        return "unsafe_response_guard"
    if _contains_restricted_care_marker(cleaned):
        return "unsafe_response_guard"
    if _is_too_similar_to_recent_assistant(cleaned, recent_logs):
        return "irrelevant_response_guard"
    shortened = _truncate_reply(cleaned)
    if not shortened:
        return "response_guard_triggered"
    if _looks_like_meta_reply(shortened):
        return "system_like_response_guard"
    if _looks_like_field_style_reply(shortened):
        return "field_leakage_guard"
    if _looks_like_scripted_reply(shortened):
        return "scripted_guidance_guard"
    if _too_much_soft_reassurance(shortened) or _looks_like_memory_test(shortened):
        return "unsafe_response_guard"
    if _contains_restricted_care_marker(shortened):
        return "unsafe_response_guard"
    if _is_too_similar_to_recent_assistant(shortened, recent_logs):
        return "irrelevant_response_guard"
    return "response_guard_triggered"


def _scenario_template_reply(
    conversation: LLMConversationInput,
    resolved: ResolvedStyleContext,
) -> str:
    """Return a deterministic repair template for known care-risk scenes."""
    if getattr(resolved.state, "care_scenario", "general") == "general":
        return ""
    return conversation_style_engine.generate_reply(resolved.strategy, resolved.context)


def _has_hard_prompt_leak(reply: str) -> bool:
    """Detect prompt/system leakage that should still force real fallback."""
    lowered = str(reply or "").lower()
    hard_markers = ("系统提示", "当前策略", "后台资料", "prompt", "system prompt", "内部指令")
    return any(marker.lower() in lowered for marker in hard_markers)


def _env_first(*keys: str) -> str:
    """Return the first non-empty environment value."""
    for key in keys:
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""


def _normalize_provider_name(provider: str) -> str:
    """Normalize provider names and keep backward-compatible defaults."""
    normalized = str(provider or "").strip().lower()
    if normalized in {"", "auto"}:
        return DEFAULT_PROVIDER
    if normalized not in {"zhipu", "deepseek", "minimax", "openai", "mock"}:
        LOGGER.warning("unknown LLM_PROVIDER '%s', fallback to mock provider", provider)
        return "mock"
    return normalized


def _resolve_provider_config(provider_override: str | None = None) -> ProviderConfig:
    """Resolve provider, key, base URL, and model from environment variables."""
    provider = _normalize_provider_name(provider_override or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER))
    if provider == "mock":
        return ProviderConfig(provider="mock", model="mock")

    if provider == "zhipu":
        return ProviderConfig(
            provider="zhipu",
            api_key=_env_first("ZHIPU_API_KEY", "OPENAI_API_KEY"),
            base_url=_env_first("ZHIPU_BASE_URL", "OPENAI_BASE_URL") or DEFAULT_PROVIDER_BASE_URLS["zhipu"],
            model=_env_first("ZHIPU_MODEL", "OPENAI_MODEL") or DEFAULT_PROVIDER_MODELS["zhipu"],
        )

    if provider == "deepseek":
        return ProviderConfig(
            provider="deepseek",
            api_key=_env_first("DEEPSEEK_API_KEY", "OPENAI_API_KEY"),
            base_url=_env_first("DEEPSEEK_BASE_URL", "OPENAI_BASE_URL") or DEFAULT_PROVIDER_BASE_URLS["deepseek"],
            model=_env_first("DEEPSEEK_MODEL", "OPENAI_MODEL") or DEFAULT_PROVIDER_MODELS["deepseek"],
        )

    if provider == "minimax":
        return ProviderConfig(
            provider="minimax",
            api_key=_env_first("MINIMAX_API_KEY", "OPENAI_API_KEY"),
            base_url=_env_first("MINIMAX_BASE_URL", "OPENAI_BASE_URL") or DEFAULT_PROVIDER_BASE_URLS["minimax"],
            model=_env_first("MINIMAX_MODEL", "OPENAI_MODEL") or DEFAULT_PROVIDER_MODELS["minimax"],
        )

    return ProviderConfig(
        provider="openai",
        api_key=_env_first("OPENAI_API_KEY"),
        base_url=_env_first("OPENAI_BASE_URL") or DEFAULT_PROVIDER_BASE_URLS["openai"],
        model=_env_first("OPENAI_MODEL") or DEFAULT_PROVIDER_MODELS["openai"],
    )


def get_provider_availability(provider_override: str | None = None) -> ProviderAvailability:
    """Return whether one provider is ready for real requests in this environment."""
    config = _resolve_provider_config(provider_override)
    if config.provider == "mock":
        return ProviderAvailability(
            provider="mock",
            available=True,
            reason="mock provider is always available",
            model=config.model,
            base_url=config.base_url,
        )

    if not config.api_key:
        return ProviderAvailability(
            provider=config.provider,
            available=False,
            reason=f"{config.provider} API key missing",
            model=config.model,
            base_url=config.base_url,
        )

    if OpenAI is None:
        return ProviderAvailability(
            provider=config.provider,
            available=False,
            reason="openai SDK unavailable",
            model=config.model,
            base_url=config.base_url,
        )

    return ProviderAvailability(
        provider=config.provider,
        available=True,
        reason="configured",
        model=config.model,
        base_url=config.base_url,
    )


def get_llm_runtime_status(provider_override: str | None = None) -> dict[str, Any]:
    """Return frontend-safe provider status without exposing credentials."""
    config = _resolve_provider_config(provider_override)
    availability = get_provider_availability(provider_override)
    return {
        "provider": config.provider,
        "model": config.model,
        "base_url": config.base_url,
        "api_key_configured": bool(config.api_key),
        "available": availability.available,
        "availability_reason": availability.reason,
        "fallback_enabled": LLM_ENABLE_FALLBACK,
        "timeout_seconds": LLM_TIMEOUT_SECONDS,
        "max_output_chars": MAX_REPLY_CHARS,
    }


def log_llm_runtime_config_once(provider_override: str | None = None, *, force: bool = False) -> None:
    """Log the active provider configuration without exposing credentials."""
    global _LLM_CONFIG_LOGGED
    if _LLM_CONFIG_LOGGED and not force:
        return
    status = get_llm_runtime_status(provider_override)
    LOGGER.warning(
        "[LLM CONFIG]\nprovider=%s\nmodel=%s\nbase_url=%s\napi_key_configured=%s\nfallback_enabled=%s\ntimeout=%s\nmax_output_chars=%s",
        status["provider"],
        status["model"],
        status["base_url"],
        str(status["api_key_configured"]).lower(),
        str(status["fallback_enabled"]).lower(),
        status["timeout_seconds"],
        status["max_output_chars"],
    )
    _LLM_CONFIG_LOGGED = True


class MockLLMService:
    """Rule-based adapter that delegates style decisions to the style engine."""

    def generate_reply(self, conversation: LLMConversationInput) -> str:
        """Generate one companion-style reply from profile and recent history."""
        return _build_mock_reply(conversation)

    def generate_reply_result(self, conversation: LLMConversationInput) -> LLMReplyResult:
        """Return mock reply metadata for evals."""
        reply = self.generate_reply(conversation)
        LOGGER.info("using mock llm")
        return LLMReplyResult(
            reply=reply,
            requested_provider="mock",
            actual_provider="mock",
            model="mock",
            fallback_used=False,
            raw_llm_reply=reply,
            safe_template_reply=reply,
        )


class ProviderSwitchingLLMService:
    """Use the configured provider when possible, otherwise fall back to mock."""

    def __init__(self, provider_override: str | None = None) -> None:
        self._provider_override = provider_override
        self._mock_service = MockLLMService()

    def _build_fallback_result(
        self,
        *,
        config: ProviderConfig,
        reply: str,
        reason: str,
        guard_triggered: bool = False,
        guard_reason: str = "",
        raw_llm_reply: str = "",
    ) -> LLMReplyResult:
        """Return the mock reply and emit a development-facing log line."""
        LOGGER.warning("fallback to mock from %s: %s", config.provider, reason)
        return LLMReplyResult(
            reply=reply,
            requested_provider=config.provider,
            actual_provider="mock",
            model=config.model or "mock",
            fallback_used=True,
            fallback_reason=reason,
            guard_triggered=guard_triggered,
            guard_reason=guard_reason,
            raw_llm_reply=raw_llm_reply,
            safe_template_reply=reply,
        )

    def _get_client(self, config: ProviderConfig) -> Any | None:
        """Build an OpenAI-compatible client when the SDK and credentials exist."""
        if not config.api_key:
            return None
        if OpenAI is None:
            LOGGER.warning("%s API key is set but the openai SDK is not installed; fallback to mock.", config.provider)
            return None
        return OpenAI(api_key=config.api_key, base_url=config.base_url)

    def _generate_real_reply_result(
        self,
        conversation: LLMConversationInput,
        config: ProviderConfig,
        mock_reference: str,
    ) -> LLMReplyResult:
        """Call one OpenAI-compatible provider and return the guarded reply."""
        client = self._get_client(config)
        if client is None:
            return self._build_fallback_result(
                config=config,
                reply=mock_reference,
                reason="client unavailable",
            )

        resolved = _resolve_style_context(conversation)
        messages = _build_real_llm_messages(conversation, resolved)
        try:
            response = client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=0.85,
                max_tokens=220,
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except Exception as timeout_error:  # pragma: no cover
            LOGGER.warning("LLM request timeout or error: %s", timeout_error)
            return self._build_fallback_result(
                config=config,
                reply=mock_reference,
                reason=f"request timeout or error: {type(timeout_error).__name__}",
            )
        
        reply = _extract_response_text(response)
        guarded = _guard_real_reply(reply, mock_reference, conversation.recent_logs)
        if guarded == mock_reference:
            guard_reason = _classify_response_guard_issue(reply, conversation.recent_logs)
            repair_reply = _scenario_template_reply(conversation, resolved)
            if repair_reply:
                LOGGER.info(
                    "using template fallback after real llm guard: provider=%s model=%s reason=%s",
                    config.provider,
                    config.model,
                    guard_reason,
                )
                return LLMReplyResult(
                    reply=repair_reply,
                    requested_provider=config.provider,
                    actual_provider="template_fallback",
                    model=config.model,
                    fallback_used=True,
                    fallback_reason=f"template_fallback: {guard_reason}",
                    guard_triggered=True,
                    guard_reason=guard_reason,
                    raw_llm_reply=reply,
                    postprocess_used=True,
                    safe_template_reply=repair_reply,
                    template_used=True,
                    template_name=getattr(resolved.state, "care_scenario", "scenario_template") or "scenario_template",
                )
            return self._build_fallback_result(
                config=config,
                reply=mock_reference,
                reason="response guard rejected real output",
                guard_triggered=True,
                guard_reason=guard_reason,
                raw_llm_reply=reply,
            )
        if _fails_direct_question_guard(conversation, guarded):
            repair_reply = _scenario_template_reply(conversation, resolved)
            if repair_reply:
                return LLMReplyResult(
                    reply=repair_reply,
                    requested_provider=config.provider,
                    actual_provider="template_fallback",
                    model=config.model,
                    fallback_used=True,
                    fallback_reason="template_fallback: direct_question_guard",
                    guard_triggered=True,
                    guard_reason="direct_question_guard",
                    raw_llm_reply=reply,
                    postprocess_used=True,
                    safe_template_reply=repair_reply,
                    template_used=True,
                    template_name=getattr(resolved.state, "care_scenario", "scenario_template") or "scenario_template",
                )
            return self._build_fallback_result(
                config=config,
                reply=mock_reference,
                reason="direct question guard rejected real output",
                guard_triggered=True,
                guard_reason="irrelevant_response_guard",
                raw_llm_reply=reply,
            )
        if _fails_relevance_guard(conversation, resolved, guarded):
            repair_reply = _scenario_template_reply(conversation, resolved)
            if repair_reply:
                return LLMReplyResult(
                    reply=repair_reply,
                    requested_provider=config.provider,
                    actual_provider="template_fallback",
                    model=config.model,
                    fallback_used=True,
                    fallback_reason="template_fallback: scenario_template_repair",
                    guard_triggered=True,
                    guard_reason="scenario_template_repair",
                    raw_llm_reply=reply,
                    postprocess_used=True,
                    safe_template_reply=repair_reply,
                    template_used=True,
                    template_name=getattr(resolved.state, "care_scenario", "scenario_template") or "scenario_template",
                )
            return self._build_fallback_result(
                config=config,
                reply=mock_reference,
                reason="relevance guard rejected real output",
                guard_triggered=True,
                guard_reason="irrelevant_response_guard",
                raw_llm_reply=reply,
            )

        LOGGER.info("using real llm: provider=%s model=%s", config.provider, config.model)
        return LLMReplyResult(
            reply=guarded,
            requested_provider=config.provider,
            actual_provider=config.provider,
            model=config.model,
            fallback_used=False,
            raw_llm_reply=reply,
            postprocess_used=_normalize_reply_text(reply) != guarded,
            safe_template_reply="",
        )

    def generate_reply_result(self, conversation: LLMConversationInput) -> LLMReplyResult:
        """Prefer the configured provider, but never allow remote failures to break chat."""
        config = _resolve_provider_config(self._provider_override)
        log_llm_runtime_config_once(self._provider_override)
        if config.provider == "mock":
            return self._mock_service.generate_reply_result(conversation)

        mock_reference = self._mock_service.generate_reply(conversation)
        if not config.api_key:
            return self._build_fallback_result(
                config=config,
                reply=mock_reference,
                reason=f"{config.provider} API key missing",
            )

        try:
            return self._generate_real_reply_result(conversation, config, mock_reference)
        except Exception as error:  # pragma: no cover - depends on network and provider state
            return self._build_fallback_result(
                config=config,
                reply=mock_reference,
                reason=f"{type(error).__name__}: {error}",
            )

    def generate_reply(self, conversation: LLMConversationInput) -> str:
        """Return only the reply text for the main chat flow."""
        return self.generate_reply_result(conversation).reply


def get_llm_service(provider_override: str | None = None) -> LLMService:
    """Return the current reply generator implementation."""
    return ProviderSwitchingLLMService(provider_override=provider_override)


def generate_llm_reply_result(
    conversation: LLMConversationInput,
    *,
    provider_override: str | None = None,
) -> LLMReplyResult:
    """Convenience helper for evals so they can compare provider outputs."""
    service = get_llm_service(provider_override=provider_override)
    return service.generate_reply_result(conversation)
