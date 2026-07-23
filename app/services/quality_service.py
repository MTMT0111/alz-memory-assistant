"""对话质量评分与照护端历史回顾服务。"""

from __future__ import annotations

from contextlib import closing
import json
import re
from typing import Any

from app.database import get_connection
from app.services import llm_service

QUALITY_TIMEOUT_SECONDS = 8
VALID_LABELS = {"优秀", "良好", "一般", "需改进"}


def _fallback_score() -> dict:
    """评分失败时的安全返回。"""
    return {"score": None, "label": "未评估", "note": "", "flags": []}


def _parse_score_json(content: str) -> dict:
    """解析模型返回的 JSON，兼容偶发 markdown 包裹。"""
    text = str(content or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        text = match.group(0)
    data = json.loads(text)

    try:
        score = float(data.get("score"))
        score = max(1.0, min(5.0, score))
    except (TypeError, ValueError):
        score = None

    label = str(data.get("label") or "未评估").strip()
    if label not in VALID_LABELS:
        label = "未评估"

    flags = data.get("flags")
    if not isinstance(flags, list):
        flags = []

    return {
        "score": score,
        "label": label,
        "note": str(data.get("note") or "").strip()[:120],
        "flags": [str(item).strip() for item in flags if str(item).strip()][:8],
    }


async def score_conversation_turn(
    user_message: str,
    assistant_response: str,
    patient_id: str,
) -> dict:
    """调用统一 LLM 入口评估单轮陪伴对话质量；失败不影响主链路。"""
    clean_user = str(user_message or "").strip()
    clean_assistant = str(assistant_response or "").strip()
    if not clean_user or not clean_assistant:
        return _fallback_score()

    system_prompt = (
        "你是阿尔兹海默症陪伴对话质量评估专家。\n"
        "请评估以下一轮对话的质量。\n"
        "只输出 JSON：\n"
        "{\n"
        "  \"score\": 1到5的浮点数,\n"
        "  \"label\": \"优秀/良好/一般/需改进\" 之一,\n"
        "  \"note\": \"一句话评估理由\",\n"
        "  \"flags\": [\"可能引发焦虑\",\"回应过于简短\"] 等问题标签数组，无问题则为[]\n"
        "}"
    )

    try:
        content = await llm_service.chat(
            system_prompt=system_prompt,
            user_message=f"患者说：{clean_user[:1200]}\nAI回复：{clean_assistant[:1600]}",
            max_tokens=180,
        )
        return _parse_score_json(content)
    except (json.JSONDecodeError, Exception):
        return _fallback_score()


async def record_scored_turn(
    *,
    patient_id: str,
    session_id: str,
    user_message: str,
    assistant_response: str,
    quality: dict,
    user_profile_id: int | None = None,
) -> None:
    """保存一轮对话及 assistant 质量结果，同时尽量回填 chat_logs 最新 assistant 行。"""
    clean_patient_id = str(patient_id or "").strip()
    clean_session_id = str(session_id or "").strip()
    if not clean_patient_id or not clean_session_id:
        return

    flags = quality.get("flags") if isinstance(quality.get("flags"), list) else []
    score = quality.get("score")
    label = str(quality.get("label") or "未评估")
    note = str(quality.get("note") or "")
    flags_text = json.dumps(flags, ensure_ascii=False)

    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO conversations (patient_id, session_id, role, content)
            VALUES (?, ?, 'user', ?)
            """,
            (clean_patient_id, clean_session_id, str(user_message or "")),
        )
        connection.execute(
            """
            INSERT INTO conversations (
                patient_id, session_id, role, content,
                quality_score, quality_label, quality_note, quality_flags
            )
            VALUES (?, ?, 'assistant', ?, ?, ?, ?, ?)
            """,
            (
                clean_patient_id,
                clean_session_id,
                str(assistant_response or ""),
                score,
                label,
                note,
                flags_text,
            ),
        )
        if user_profile_id:
            connection.execute(
                """
                UPDATE chat_logs
                SET quality_score = ?, quality_label = ?, quality_note = ?
                WHERE id = (
                    SELECT id FROM chat_logs
                    WHERE user_id = ? AND role = 'assistant'
                    ORDER BY id DESC
                    LIMIT 1
                )
                """,
                (score, label, note, int(user_profile_id)),
            )
        connection.commit()


def _decode_flags(value: Any) -> list[str]:
    """从 quality_flags 文本解析问题标签。"""
    try:
        data = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(item).strip() for item in data if str(item).strip()]


async def get_session_summary(patient_id: str, session_id: str) -> dict:
    """返回某个 session 的 assistant 质量均分、轮数和去重 flags。"""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT quality_score, quality_flags
            FROM conversations
            WHERE patient_id = ? AND session_id = ? AND role = 'assistant'
            ORDER BY timestamp ASC, id ASC
            """,
            (str(patient_id), str(session_id)),
        ).fetchall()

    scores = [float(row["quality_score"]) for row in rows if row["quality_score"] is not None]
    flags: list[str] = []
    for row in rows:
        for flag in _decode_flags(row["quality_flags"]):
            if flag not in flags:
                flags.append(flag)

    return {
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        "turn_count": len(rows),
        "flags": flags,
    }


async def get_chat_history(patient_id: str, limit: int = 20) -> list[dict]:
    """读取最近 N 条对话记录，按时间倒序。"""
    safe_limit = max(1, min(int(limit or 20), 200))
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT session_id, role, content, timestamp, quality_score, quality_label, quality_note, quality_flags
            FROM conversations
            WHERE patient_id = ?
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (str(patient_id), safe_limit),
        ).fetchall()

    return [
        {
            "session_id": row["session_id"],
            "role": row["role"],
            "content": row["content"],
            "timestamp": row["timestamp"],
            "quality_score": row["quality_score"],
            "quality_label": row["quality_label"],
            "quality_note": row["quality_note"] or "",
            "flags": _decode_flags(row["quality_flags"]),
        }
        for row in rows
    ]


async def list_session_summaries(patient_id: str, limit: int = 20) -> list[dict]:
    """按 session_id 返回最近会话摘要。"""
    safe_limit = max(1, min(int(limit or 20), 100))
    with closing(get_connection()) as connection:
        session_rows = connection.execute(
            """
            SELECT session_id, MIN(timestamp) AS date, MAX(timestamp) AS last_time
            FROM conversations
            WHERE patient_id = ?
            GROUP BY session_id
            ORDER BY last_time DESC
            LIMIT ?
            """,
            (str(patient_id), safe_limit),
        ).fetchall()

    summaries = []
    for row in session_rows:
        summary = await get_session_summary(str(patient_id), str(row["session_id"]))
        summaries.append(
            {
                "session_id": row["session_id"],
                "date": row["date"],
                "turn_count": summary["turn_count"],
                "avg_score": summary["avg_score"],
                "flags": summary["flags"],
            }
        )
    return summaries
