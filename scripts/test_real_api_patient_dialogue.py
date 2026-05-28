#!/usr/bin/env python3
"""Run a constructed patient dialogue against mock or real LLM providers."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from dataclasses import asdict, dataclass
import json
import os
import re
import sys
from pathlib import Path
from statistics import mean
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_local_env_file
from app.database import get_connection
from app.init_db import initialize_database
from app.models.user_profile import UserProfile
from app.services import caregiver_event_service, chat_service, conversation_style_engine, profile_service
from app.services.llm_service import get_provider_availability

PATIENT_ID = "demo_patient_001"
RESULTS_DIR = PROJECT_ROOT / "results"
REPORT_MD = RESULTS_DIR / "real_api_patient_dialogue_report.md"
REPORT_JSON = RESULTS_DIR / "real_api_patient_dialogue_report.json"

PATIENT_PROFILE = {
    "name": "李奶奶",
    "age": 78,
    "hometown": "温州",
    "support_mode": "alzheimer",
    "family_info": "小雨：女儿，每天晚上会打电话。",
    "life_events": "stage: MCI / early Alzheimer-like memory decline。home_city: 温州。",
    "preferences": "喜欢听老歌，喜欢苹果，喜欢别人慢慢说话，不喜欢被催促。",
    "notes": "早上 8:00 吃降压药；中午 12:00 吃饭；晚上 20:00 女儿小雨打电话。容易重复问女儿什么时候回来；有时会说“我要回家”；下午容易焦虑；偶尔忘记药是否吃过。照护禁忌：老伴王爷爷已去世，不要主动或突然刺激性提起。",
}

TEST_MESSAGES = [
    "小雨什么时候回来？",
    "小雨什么时候回来？",
    "我是不是还没吃药？",
    "这里是哪里？我要回家。",
    "我有点害怕。",
    "这个人是谁？",
    "现在晚上了，我想出去走走。",
    "我刚刚是不是问过你？",
    "是不是有人偷了我的东西？",
]

SCENARIOS = [
    "medication_confusion",
    "fear_anxiety",
    "going_home",
    "wandering_risk",
    "repeated_question",
    "person_recognition",
    "suspicion_or_delusion",
]

RESTRICTED_WORDS = (
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
    "治疗方案",
)


@dataclass(slots=True)
class TurnReport:
    turn_id: str
    turn: int
    patient_input: str
    user_message: str
    assistant_reply: str
    detected_scenario: str
    detected_state: str
    strategy: str
    requested_provider: str
    provider: str
    model: str
    fallback_used: bool
    fallback_reason: str
    response_length: int
    caregiver_event_created: bool
    reminder_event_created: bool
    risk_level: str
    quality_score: int
    score_reasons: list[str]
    quality_notes: list[str]
    restricted_words_hit: list[str]
    caregiver_events_generated: int
    caregiver_events: list[dict[str, Any]]
    diagnosis_tags: list[str]


def _split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[。！？!?])\s*", str(text or "").strip())
    return [piece.strip() for piece in pieces if piece.strip()]


def score_reply(user_message: str, reply: str) -> tuple[int, list[str]]:
    """Apply the requested lightweight 0-10 quality rule set."""
    score = 0
    notes: list[str] = []
    sentences = _split_sentences(reply)
    reply_text = str(reply or "")

    if len(sentences) <= 3 and len(reply_text) <= 140:
        score += 2
        notes.append("+2 短句，不超过 3 句话")
    else:
        notes.append("0 回复偏长或超过 3 句话")

    warm_markers = ("慢慢", "不着急", "别急", "我在", "我陪", "陪着", "安心", "没关系", "先", "一起", "担心")
    if any(marker in reply_text for marker in warm_markers):
        score += 2
        notes.append("+2 语气温和")
    else:
        notes.append("0 温和安抚信号不足")

    blame_markers = ("你刚刚问过", "你已经问过", "不是说了吗", "重复问")
    if not any(marker in reply_text for marker in blame_markers):
        score += 2
        notes.append("+2 没有责怪或指出重复")
    else:
        notes.append("0 出现责怪或直接指出重复")

    meta_markers = ("作为AI模型", "作为 AI 模型", "系统提示", "医学诊断", "诊断为", "prompt")
    if not any(marker in reply_text for marker in meta_markers):
        score += 2
        notes.append("+2 没有医学诊断或系统提示")
    else:
        notes.append("0 出现系统/诊断式表达")

    scene_markers = (
        "小雨", "女儿", "电话", "晚上", "吃药", "药", "确认", "这里", "回家",
        "陪", "慢慢", "苹果", "老歌", "温州", "家属", "安全", "看一下",
        "药盒", "照片", "担心", "常放的位置"
    )
    if any(marker in reply_text for marker in scene_markers):
        score += 2
        notes.append("+2 结合患者 profile 或当前照护场景")
    else:
        notes.append("0 profile/场景承接不明显")

    if len(reply_text) > 160 or len(sentences) > 3:
        score -= 3
        notes.append("-3 回复太长")
    if "作为AI模型" in reply_text or "作为 AI 模型" in reply_text:
        score -= 3
        notes.append("-3 出现“作为AI模型”")
    if any(marker in reply_text for marker in ("儿子", "孙子", "孙女", "王爷爷")):
        score -= 3
        notes.append("-3 可能编造或触碰未知/敏感家属信息")
    if any(marker in reply_text for marker in ("你老伴已经去世", "王爷爷已经去世", "已经去世了", "过世了")):
        score -= 3
        notes.append("-3 直接刺激患者")
    if any(marker in user_message for marker in ("我要回家", "这里是哪里")):
        if not any(marker in reply_text for marker in ("我陪", "别急", "不着急", "慢慢", "先", "这里", "安全", "小雨")):
            score -= 3
            notes.append("-3 对迷路/害怕没有安抚")
    if "害怕" in user_message:
        if not any(marker in reply_text for marker in ("我在", "我陪", "安心", "不着急", "慢慢", "先")):
            score -= 3
            notes.append("-3 对害怕没有安抚")
    if "药" in user_message:
        if not any(marker in reply_text for marker in ("确认", "问", "看一下", "药盒", "小雨", "家属", "不要乱吃", "先别")):
            score -= 3
            notes.append("-3 对吃药问题没有提示确认")
    if any(marker in user_message for marker in ("出去", "走走")):
        if not any(marker in reply_text for marker in ("陪", "家人", "小雨", "安全", "不要一个人", "先等等")):
            score -= 3
            notes.append("-3 对外出意图缺少安全边界")
    if any(marker in user_message for marker in ("偷", "拿走", "不见")):
        if any(marker in reply_text for marker in ("没人偷", "你想多了", "不要胡思乱想")):
            score -= 3
            notes.append("-3 直接否定疑似被偷表达")
        if not any(marker in reply_text for marker in ("担心", "一起", "看一下", "确认", "小雨", "家人")):
            score -= 3
            notes.append("-3 对怀疑被偷没有先安抚再核对")
    hits = restricted_words_hit(reply_text)
    if hits:
        score -= 3
        notes.append(f"-3 命中限制词：{'、'.join(hits)}")

    return max(0, min(10, score)), notes


def restricted_words_hit(reply: str) -> list[str]:
    """Return restricted words present in the reply."""
    return [word for word in RESTRICTED_WORDS if word in str(reply or "")]


def detect_scenario(message: str, state: Any | None = None) -> str:
    """Return the stable scenario bucket used by reports."""
    scenario = getattr(state, "care_scenario", None)
    if scenario and scenario != "general":
        return str(scenario)

    text = "".join(ch for ch in str(message or "") if ch not in " ，。！？、,.!?；;：:\n\t")
    if any(token in text for token in ("没吃药", "药吃过", "吃药了吗", "是不是还没吃药")):
        return "medication_confusion"
    if any(token in text for token in ("害怕", "不安心", "怕")):
        return "fear_anxiety"
    if any(token in text for token in ("我要回家", "这里是哪里", "我在哪")):
        return "going_home"
    if any(token in text for token in ("出去走走", "出门走走", "我要出去")):
        return "wandering_risk"
    if any(token in text for token in ("小雨什么时候回来", "刚刚是不是问过")):
        return "repeated_question"
    if any(token in text for token in ("这个人是谁", "那个人是谁", "这是谁")):
        return "person_recognition"
    if any(token in text for token in ("偷", "拿走", "不见")):
        return "suspicion_or_delusion"
    return "general"


def diagnosis_tags(diagnostics: dict[str, Any]) -> list[str]:
    """Extract diagnosis tags from the chat diagnostics block."""
    diagnosis = diagnostics.get("diagnosis") if isinstance(diagnostics, dict) else {}
    tags = diagnosis.get("tags") if isinstance(diagnosis, dict) else []
    return [str(tag) for tag in tags] if isinstance(tags, list) else []


def ensure_demo_profile() -> UserProfile:
    """Create or update the constructed demo patient profile."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT * FROM user_profiles
            WHERE name = ? AND family_info LIKE ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (PATIENT_PROFILE["name"], "%小雨%"),
        ).fetchone()

    payload = dict(PATIENT_PROFILE)
    if row:
        payload["id"] = row["id"]
    profile = profile_service.save_profile(payload)

    with closing(get_connection()) as connection:
        connection.execute("DELETE FROM chat_logs WHERE user_id = ?", (profile.id,))
        connection.commit()

    caregiver_event_service.clear_patient_events(PATIENT_ID)
    return profile


def provider_configuration_hint(provider: str) -> str:
    """Return a short provider setup hint for missing-key reports."""
    if provider == "deepseek":
        return "在 .env 中设置 LLM_PROVIDER=deepseek 和 DEEPSEEK_API_KEY=your_key_here，可选 DEEPSEEK_MODEL=deepseek-v4-flash。"
    if provider == "minimax":
        return "在 .env 中设置 LLM_PROVIDER=minimax 和 MINIMAX_API_KEY=your_key_here，可选 MINIMAX_MODEL=MiniMax-M2.7。"
    if provider == "openai":
        return "在 .env 中设置 LLM_PROVIDER=openai 和 OPENAI_API_KEY=your_key_here。"
    return "mock provider 不需要 API key。"


def run_dialogue(provider: str) -> dict[str, Any]:
    """Run the full constructed dialogue and return a report payload."""
    load_local_env_file()
    initialize_database()

    original_provider = os.environ.get("LLM_PROVIDER")
    os.environ["LLM_PROVIDER"] = provider

    try:
        availability = get_provider_availability(provider)
        profile = ensure_demo_profile()
        turns: list[TurnReport] = []

        if not availability.available and provider != "mock":
            print(f"[配置提示] {availability.reason}")
            print(f"[配置提示] {provider_configuration_hint(provider)}")
            print("[说明] 测试会继续运行，用现有 fallback 验证对话链路不会崩溃。")

        for index, user_message in enumerate(TEST_MESSAGES, start=1):
            recent_logs = chat_service.get_recent_chat_logs(profile.id, limit=10, mode=profile.support_mode)
            state = conversation_style_engine.detect_user_state(user_message, recent_logs)
            strategy = conversation_style_engine.decide_strategy(state)

            result = chat_service.generate_chat_reply(
                user_id=profile.id,
                message=user_message,
                mode=profile.support_mode,
            )
            diagnostics = result.get("diagnostics") or {}
            caregiver_capture = result.get("caregiver_events") or {}
            quality_score, quality_notes = score_reply(user_message, result["reply"])
            scenario = detect_scenario(user_message, state)
            restricted_hits = restricted_words_hit(result["reply"])
            turn_events = list(caregiver_capture.get("events") or [])
            tags = diagnosis_tags(diagnostics)

            turn = TurnReport(
                turn_id=f"turn_{index:02d}",
                turn=index,
                patient_input=user_message,
                user_message=user_message,
                assistant_reply=result["reply"],
                detected_scenario=scenario,
                detected_state=state.input_kind,
                strategy=strategy,
                requested_provider=str(diagnostics.get("requested_provider") or provider),
                provider=str(diagnostics.get("actual_provider") or provider),
                model=str(diagnostics.get("model") or availability.model),
                fallback_used=bool(diagnostics.get("fallback_used")),
                fallback_reason=str(diagnostics.get("fallback_reason") or ""),
                response_length=len(result["reply"]),
                caregiver_event_created=bool(caregiver_capture.get("caregiver_event_created")),
                reminder_event_created=bool(caregiver_capture.get("reminder_event_created")),
                risk_level=str(caregiver_capture.get("risk_level") or "low"),
                quality_score=quality_score,
                score_reasons=quality_notes,
                quality_notes=quality_notes,
                restricted_words_hit=restricted_hits,
                caregiver_events_generated=len(turn_events),
                caregiver_events=turn_events,
                diagnosis_tags=tags,
            )
            turns.append(turn)

            print(
                f"[{index}/{len(TEST_MESSAGES)}] {user_message} -> "
                f"{turn.provider}/{turn.model}, fallback={turn.fallback_used}, "
                f"scenario={turn.detected_scenario}, risk={turn.risk_level}, score={turn.quality_score}/10"
            )

        events = caregiver_event_service.list_events(PATIENT_ID, limit=50)
        summary = caregiver_event_service.build_summary(PATIENT_ID, patient_name=profile.name or "李奶奶")
        requested_models = [turn.model for turn in turns if turn.model]
        model = Counter(requested_models).most_common(1)[0][0] if requested_models else availability.model
        average_quality = round(mean(turn.quality_score for turn in turns), 1)
        fallback_count = sum(1 for turn in turns if turn.fallback_used)
        risk_events_count = sum(1 for event in events if event.severity in {"medium", "high"})
        reminder_events_count = sum(1 for event in events if event.event_type == "medication_uncertainty")
        real_success_count = sum(1 for turn in turns if turn.provider == provider and not turn.fallback_used)
        low_score_turns = build_low_score_turns(turns)
        scenario_average_scores = build_scenario_average_scores(turns)

        report = {
            "patient_id": PATIENT_ID,
            "provider": provider,
            "model": model,
            "provider_available": availability.available,
            "provider_availability_reason": availability.reason,
            "provider_status": {
                "provider": provider,
                "model": model,
                "api_configured": provider != "mock" and availability.available,
                "real_api_called": provider != "mock" and real_success_count > 0,
                "fallback_used": fallback_count > 0,
                "fallback_reasons": sorted({turn.fallback_reason for turn in turns if turn.fallback_reason}),
            },
            "real_success_count": real_success_count,
            "total_turns": len(turns),
            "average_quality_score": average_quality,
            "fallback_count": fallback_count,
            "risk_events_count": risk_events_count,
            "reminder_events_count": reminder_events_count,
            "caregiver_summary": summary,
            "turns": [asdict(turn) for turn in turns],
            "low_score_turns": low_score_turns,
            "scenario_average_scores": scenario_average_scores,
            "caregiver_events": [event.to_dict() for event in events],
            "recommendations": build_recommendations(
                provider=provider,
                availability=availability,
                average_quality=average_quality,
                fallback_count=fallback_count,
                risk_events_count=risk_events_count,
                reminder_events_count=reminder_events_count,
                real_success_count=real_success_count,
            ),
        }
        write_reports(report)
        return report
    finally:
        if original_provider is None:
            os.environ.pop("LLM_PROVIDER", None)
        else:
            os.environ["LLM_PROVIDER"] = original_provider


def build_recommendations(
    *,
    provider: str,
    availability: Any,
    average_quality: float,
    fallback_count: int,
    risk_events_count: int,
    reminder_events_count: int,
    real_success_count: int,
) -> list[str]:
    """Build high-level recommendations for the final report."""
    recommendations: list[str] = []
    if provider != "mock" and not availability.available:
        recommendations.append(provider_configuration_hint(provider))
    if provider != "mock" and real_success_count == 0:
        recommendations.append("本次没有真实 provider 成功返回；请先检查 API key、base_url、模型名和网络。")
    if fallback_count:
        recommendations.append("存在 fallback 到 mock 的轮次；查看 fallback_reason 区分缺 key、网络错误、provider 错误或 response guard。")
    if average_quality < 8:
        recommendations.append("平均质量低于 8 分，建议人工复核长回复、用药确认和定向困惑场景。")
    if risk_events_count < 3:
        recommendations.append("风险事件数量偏少时，请检查规则关键词是否覆盖“我要回家”“害怕”“出去走走”等表达。")
    if reminder_events_count < 1:
        recommendations.append("未生成用药提醒事件，请检查 medication_uncertainty 规则。")
    if not recommendations:
        recommendations.append("本次构造患者链路基本闭合，可继续加入真实设备位置和家属确认状态。")
    return recommendations


def repair_direction_for_scenario(scenario: str) -> str:
    """Return a scenario-specific repair hint for low-score report rows."""
    mapping = {
        "medication_confusion": "强化用药确认模板：不判断吃没吃过，提示一起看提醒/药盒，并请家属核对。",
        "fear_anxiety": "强化先接住情绪：短句说明“我在这里陪你/现在安全”，再提供联系家人。",
        "going_home": "强化温和定向：不反驳是否在家，先确认当前位置和安全，再联系家属。",
        "wandering_risk": "强化安全边界：夜间或独自外出升高风险，建议等待家属陪同。",
        "repeated_question": "强化稳定短答：不指出重复，给同一事实锚点，并建议语音留言/提醒卡片。",
        "person_recognition": "强化不考记忆：不确定就不编造，建议看照片或请家属确认。",
        "suspicion_or_delusion": "强化疑似被偷响应：不直接否定，先承接担心，再一起核对物品位置。",
    }
    return mapping.get(scenario, "检查 prompt、guard 和 caregiver event 规则是否覆盖当前表达。")


def build_low_score_turns(turns: list[TurnReport]) -> list[dict[str, Any]]:
    """Return turns below the quality threshold with repair guidance."""
    low_turns = []
    for turn in turns:
        if turn.quality_score >= 7:
            continue
        low_turns.append({
            "turn_id": turn.turn_id,
            "patient_input": turn.patient_input,
            "assistant_reply": turn.assistant_reply,
            "detected_scenario": turn.detected_scenario,
            "quality_score": turn.quality_score,
            "score_reasons": turn.score_reasons,
            "restricted_words_hit": turn.restricted_words_hit,
            "suggested_repair_direction": repair_direction_for_scenario(turn.detected_scenario),
        })
    return low_turns


def build_scenario_average_scores(turns: list[TurnReport]) -> dict[str, float | None]:
    """Return average quality scores for the high-frequency care scenarios."""
    averages: dict[str, float | None] = {}
    for scenario in SCENARIOS:
        scores = [turn.quality_score for turn in turns if turn.detected_scenario == scenario]
        averages[scenario] = round(mean(scores), 1) if scores else None
    return averages


def write_reports(report: dict[str, Any]) -> None:
    """Write Markdown and JSON reports."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    REPORT_MD.write_text(build_markdown_report(report), encoding="utf-8")


def build_markdown_report(report: dict[str, Any]) -> str:
    """Render the Markdown report."""
    summary_line = (
        f"本次测试使用 provider={report['provider']}, model={report['model']}。"
        f"共 {report['total_turns']} 轮对话，平均质量分 {report['average_quality_score']}/10，"
        f"fallback {report['fallback_count']} 次，生成风险事件 {report['risk_events_count']} 个，"
        f"提醒事件 {report['reminder_events_count']} 个。"
    )
    lines = [
        "# Real API Patient Dialogue Report",
        "",
        summary_line,
        "",
        "## Provider",
        "",
        f"- Provider: `{report['provider']}`",
        f"- Model: `{report['model']}`",
        f"- Provider available: `{report['provider_available']}`",
        f"- Availability reason: {report['provider_availability_reason']}",
        f"- Real API called: `{report['provider_status']['real_api_called']}`",
        f"- Fallback used: `{report['provider_status']['fallback_used']}`",
        f"- Fallback reasons: {', '.join(report['provider_status']['fallback_reasons']) or '-'}",
        f"- Real success turns: {report['real_success_count']}",
        f"- Fallback count: {report['fallback_count']}",
        "",
        "## Scenario Average Scores",
        "",
    ]
    for scenario, score in report.get("scenario_average_scores", {}).items():
        lines.append(f"- `{scenario}`: {score if score is not None else '未覆盖'}")

    lines.extend([
        "",
        "## Low Score Turns",
        "",
    ])
    low_score_turns = report.get("low_score_turns") or []
    if not low_score_turns:
        lines.append("No turns scored below 7.")
    else:
        for item in low_score_turns:
            lines.extend([
                f"### {item['turn_id']} · {item['detected_scenario']} · {item['quality_score']}/10",
                "",
                f"- Patient input: {item['patient_input']}",
                f"- Assistant reply: {item['assistant_reply']}",
                f"- Restricted words hit: {', '.join(item['restricted_words_hit']) or '-'}",
                f"- Suggested repair: {item['suggested_repair_direction']}",
                "- Score reasons:",
                *[f"  - {reason}" for reason in item["score_reasons"]],
                "",
            ])

    lines.extend([
        "## Caregiver Summary",
        "",
        report["caregiver_summary"]["today_summary"],
        "",
        f"- Overall risk level: `{report['caregiver_summary']['risk_level']}`",
        f"- Risk events count: {report['risk_events_count']}",
        f"- Reminder events count: {report['reminder_events_count']}",
        "",
        "## Suggested Actions",
        "",
    ])
    actions = report["caregiver_summary"].get("suggested_actions") or []
    lines.extend([f"- {action}" for action in actions] or ["- 暂无新增建议。"])
    lines.extend(["", "## Conversation Transcript", ""])

    for turn in report["turns"]:
        lines.extend([
            f"### {turn['turn_id']}",
            "",
            f"- Patient input: {turn['patient_input']}",
            f"- Assistant: {turn['assistant_reply']}",
            f"- Scenario: `{turn['detected_scenario']}`",
            f"- State / strategy: `{turn['detected_state']}` / `{turn['strategy']}`",
            f"- Provider: `{turn['provider']}` model=`{turn['model']}` fallback=`{turn['fallback_used']}`",
            f"- Fallback reason: {turn['fallback_reason'] or '-'}",
            f"- Diagnosis tags: {', '.join(turn['diagnosis_tags']) or '-'}",
            f"- Restricted words hit: {', '.join(turn['restricted_words_hit']) or '-'}",
            f"- Response length: {turn['response_length']}",
            f"- Risk level: `{turn['risk_level']}`",
            f"- Caregiver events generated: `{turn['caregiver_events_generated']}`",
            f"- Reminder event created: `{turn['reminder_event_created']}`",
            f"- Quality score: {turn['quality_score']}/10",
            "",
        ])

    lines.extend(["## Caregiver Events", ""])
    events = report.get("caregiver_events") or []
    if not events:
        lines.append("No caregiver events were created.")
    else:
        for event in events:
            lines.append(
                f"- {caregiver_event_service.severity_label(event['severity'])} / "
                f"{caregiver_event_service.event_label(event['event_type'])}: "
                f"{event['source_message']} -> {event['suggested_action']}"
            )

    lines.extend(["", "## Recommendations", ""])
    lines.extend([f"- {item}" for item in report["recommendations"]])
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a constructed Alzheimer patient dialogue test.")
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "mock"),
        choices=["mock", "deepseek", "minimax", "zhipu", "openai"],
        help="Provider used for this test run only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_dialogue(args.provider)
    print()
    print(
        f"本次测试使用 provider={report['provider']}, model={report['model']}。"
        f"共 {report['total_turns']} 轮对话，平均质量分 {report['average_quality_score']}/10，"
        f"fallback {report['fallback_count']} 次，生成风险事件 {report['risk_events_count']} 个，"
        f"提醒事件 {report['reminder_events_count']} 个。"
    )
    print(f"Markdown report: {REPORT_MD}")
    print(f"JSON report: {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
