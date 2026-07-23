"""对话风险信号分析与风险事件记录服务。"""

from __future__ import annotations

import asyncio
from contextlib import closing
from datetime import datetime, timedelta
import json
import re
from typing import Any

from app.database import get_connection
from app.services import llm_service, notify_service, patient_service

RISK_TIMEOUT_SECONDS = 8
RISK_LEVELS = {"低", "中", "高"}
RISK_TYPES = {"跌倒风险", "用药混乱", "情绪危机", "走失风险", "其他"}


def _fallback_result() -> dict:
    """风险检测失败时的安全返回。"""
    return {"has_risk": False}


def _parse_risk_json(content: str) -> dict:
    """解析模型返回的风险 JSON，兼容 markdown 包裹。"""
    text = str(content or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        text = match.group(0)
    data = json.loads(text)

    risk_level = str(data.get("risk_level") or "").strip() or None
    if risk_level not in RISK_LEVELS:
        risk_level = None
    risk_type = str(data.get("risk_type") or "").strip() or None
    if risk_type not in RISK_TYPES:
        risk_type = "其他" if risk_type else None
    return {
        "has_risk": bool(data.get("has_risk")) and risk_level is not None,
        "risk_level": risk_level,
        "risk_type": risk_type,
        "evidence": str(data.get("evidence") or "").strip()[:300],
        "suggestion": str(data.get("suggestion") or "").strip()[:300],
    }


async def analyze_risk(
    user_message: str,
    assistant_response: str,
    patient_id: str,
    session_id: str,
) -> dict:
    """用统一 LLM 入口分析一轮对话里的照护安全风险信号。"""
    clean_user = str(user_message or "").strip()
    clean_assistant = str(assistant_response or "").strip()
    if not clean_user and not clean_assistant:
        return _fallback_result()

    system_prompt = (
        "你是阿尔兹海默症照护安全专家。\n"
        "分析以下对话，判断患者是否表现出以下风险信号。\n"
        "只输出 JSON：\n"
        "{\n"
        "  \"has_risk\": true或false,\n"
        "  \"risk_level\": \"低/中/高\" 或 null,\n"
        "  \"risk_type\": \"跌倒风险/用药混乱/情绪危机/走失风险/其他\" 或 null,\n"
        "  \"evidence\": \"触发判断的原文片段\" 或 \"\",\n"
        "  \"suggestion\": \"给照护者的一句建议\" 或 \"\"\n"
        "}\n"
        "风险信号包括：提到疼痛/头晕/跌倒、对用药感到困惑、"
        "表现出强烈焦虑或悲伤、提到想出门但分不清方向、"
        "出现明显的时间/地点混乱。"
    )

    try:
        content = await llm_service.chat(
            system_prompt=system_prompt,
            user_message=(
                f"patient_id：{patient_id}\n"
                f"session_id：{session_id}\n"
                f"患者说：{clean_user[:1200]}\n"
                f"AI回复：{clean_assistant[:1600]}"
            ),
            max_tokens=180,
        )
        return _parse_risk_json(content)
    except (json.JSONDecodeError, Exception):
        return _fallback_result()


async def record_risk_event(
    patient_id: str,
    session_id: str,
    risk_level: str,
    risk_type: str,
    evidence: str,
    suggestion: str,
) -> None:
    """写入中/高风险事件，供照护端 dashboard 展示。"""
    clean_patient_id = str(patient_id or "").strip()
    clean_session_id = str(session_id or "").strip()
    clean_level = str(risk_level or "").strip()
    if not clean_patient_id or not clean_session_id or clean_level not in {"中", "高"}:
        return

    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO risk_events (
                patient_id, session_id, risk_level, risk_type,
                evidence, suggestion, is_resolved
            )
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (
                clean_patient_id,
                clean_session_id,
                clean_level,
                str(risk_type or "其他").strip() or "其他",
                str(evidence or "").strip(),
                str(suggestion or "").strip(),
            ),
        )
        connection.commit()

    if clean_level == "高":
        patient = await patient_service.get_patient(clean_patient_id)
        patient_name = str(patient.get("name") if patient else clean_patient_id)
        asyncio.create_task(
            notify_service.notify_high_risk(
                patient_name,
                str(risk_type or "其他").strip() or "其他",
                str(suggestion or "").strip(),
            )
        )


async def list_risk_events(
    patient_id: str,
    days: int = 7,
    unresolved_only: bool = True,
) -> list[dict]:
    """返回最近 N 天风险事件，可筛选未处理。"""
    clean_patient_id = str(patient_id or "").strip()
    if not clean_patient_id:
        return []
    safe_days = max(1, min(int(days or 7), 90))
    since = (datetime.now() - timedelta(days=safe_days - 1)).date().isoformat()
    resolved_sql = "AND is_resolved = 0" if unresolved_only else ""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            f"""
            SELECT id, patient_id, session_id, risk_level, risk_type,
                   evidence, suggestion, is_resolved, created_at
            FROM risk_events
            WHERE patient_id = ?
              AND substr(created_at, 1, 10) >= ?
              {resolved_sql}
            ORDER BY is_resolved ASC, created_at DESC, id DESC
            """,
            (clean_patient_id, since),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


async def resolve_risk_event(event_id: int) -> bool:
    """标记风险事件已处理。"""
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "UPDATE risk_events SET is_resolved = 1 WHERE id = ?",
            (int(event_id),),
        )
        connection.commit()
    return int(cursor.rowcount or 0) > 0


def _row_to_dict(row: Any) -> dict:
    """SQLite Row 转 API 字典。"""
    return {
        "id": row["id"],
        "patient_id": row["patient_id"],
        "session_id": row["session_id"],
        "risk_level": row["risk_level"],
        "risk_type": row["risk_type"] or "其他",
        "evidence": row["evidence"] or "",
        "suggestion": row["suggestion"] or "",
        "created_at": row["created_at"],
        "is_resolved": int(row["is_resolved"] or 0),
    }
