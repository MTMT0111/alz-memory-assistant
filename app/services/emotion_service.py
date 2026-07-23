"""患者单轮对话情绪分析与每日情绪写入服务。"""

from __future__ import annotations

from contextlib import closing
from datetime import date
import json
import re

from app.database import get_connection
from app.services import llm_service

EMOTION_TIMEOUT_SECONDS = 8
VALID_MOOD_LABELS = {"低落", "平稳", "愉快", "焦虑", "困惑"}


def _today_text() -> str:
    """返回今天日期，用于更新 daily_care_summary。"""
    return date.today().isoformat()


def _fallback_result() -> dict:
    """情绪分析失败时的安全返回。"""
    return {
        "mood_score": None,
        "mood_label": "未知",
        "evidence": "",
        "confidence": 0,
    }


def _parse_json_payload(text: str) -> dict:
    """解析模型返回的 JSON，兼容偶发的 markdown 包裹。"""
    content = str(text or "").strip()
    content = re.sub(r"^```(?:json)?", "", content).strip()
    content = re.sub(r"```$", "", content).strip()
    match = re.search(r"\{.*\}", content, flags=re.S)
    if match:
        content = match.group(0)
    data = json.loads(content)

    mood_score = data.get("mood_score")
    try:
        mood_score = float(mood_score)
        mood_score = max(1.0, min(5.0, mood_score))
    except (TypeError, ValueError):
        mood_score = None

    mood_label = str(data.get("mood_label") or "未知").strip()
    if mood_label not in VALID_MOOD_LABELS:
        mood_label = "未知"

    try:
        confidence = float(data.get("confidence") or 0)
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0

    return {
        "mood_score": mood_score,
        "mood_label": mood_label,
        "evidence": str(data.get("evidence") or "").strip(),
        "confidence": confidence,
    }


def _ensure_daily_mood_columns() -> None:
    """兼容旧库：确保每日摘要表存在情绪标签和证据列。"""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(daily_care_summary)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}
        if "mood_label" not in existing_columns:
            connection.execute("ALTER TABLE daily_care_summary ADD COLUMN mood_label TEXT")
        if "mood_evidence" not in existing_columns:
            connection.execute("ALTER TABLE daily_care_summary ADD COLUMN mood_evidence TEXT")
        connection.commit()


async def analyze_emotion(conversation_text: str, patient_id: str) -> dict:
    """将最近一次患者发言发给统一 LLM 入口，返回轻量情绪评估。"""
    clean_text = str(conversation_text or "").strip()
    if not clean_text:
        return _fallback_result()

    system_prompt = (
        "你是一个专业的老年心理健康评估助手。\n"
        "根据以下患者发言，评估患者当前情绪状态。\n"
        "只输出 JSON，不输出其他任何内容：\n"
        "{\n"
        "  \"mood_score\": 1到5的浮点数（1=非常低落，3=平稳，5=非常愉快）,\n"
        "  \"mood_label\": \"低落\" 或 \"平稳\" 或 \"愉快\" 或 \"焦虑\" 或 \"困惑\",\n"
        "  \"evidence\": \"支持判断的1句话原文引用或说明\",\n"
        "  \"confidence\": 0到1的浮点数\n"
        "}"
    )

    try:
        content = await llm_service.chat(
            system_prompt=system_prompt,
            user_message=clean_text[:1200],
            max_tokens=180,
        )
        parsed = _parse_json_payload(content)
        parsed["patient_id"] = str(patient_id or "")
        return parsed
    except (json.JSONDecodeError, Exception):
        return _fallback_result()


async def update_daily_mood(
    patient_id: str,
    mood_score: float,
    mood_label: str,
    evidence: str = "",
) -> None:
    """更新当天情绪字段；没有当天记录时先创建。"""
    clean_patient_id = str(patient_id or "").strip()
    if not clean_patient_id:
        return

    try:
        normalized_score = float(mood_score)
        normalized_score = max(1.0, min(5.0, normalized_score))
    except (TypeError, ValueError):
        return

    normalized_label = str(mood_label or "未知").strip() or "未知"
    clean_evidence = str(evidence or "").strip()[:200]
    today = _today_text()
    _ensure_daily_mood_columns()
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO daily_care_summary (
                patient_id, date, mood_score, mood_label, mood_evidence
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(patient_id, date) DO UPDATE SET
                mood_score = excluded.mood_score,
                mood_label = excluded.mood_label,
                mood_evidence = excluded.mood_evidence
            """,
            (clean_patient_id, today, normalized_score, normalized_label, clean_evidence),
        )
        connection.commit()
