"""单日照护摘要持久化与跨日趋势查询服务。"""

from __future__ import annotations

from contextlib import closing
from datetime import date, datetime
import re
from typing import Any

from app.database import get_connection
from app.services import llm_service, profile_service


def _today_text() -> str:
    """返回本地日期字符串，用作 daily_care_summary 的 date。"""
    return date.today().isoformat()


def _profile_id_for_patient(patient_id: str) -> int:
    """将 caregiver patient_id 映射到现有 user_profiles.id。"""
    clean_id = str(patient_id or "").strip()
    if clean_id.isdigit():
        return int(clean_id)
    if clean_id.startswith("profile_"):
        suffix = clean_id.split("_", 1)[1]
        return int(suffix) if suffix.isdigit() else 0

    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    return int(profile.id or 0)


def _today_bounds(today: str) -> tuple[str, str]:
    """SQLite 文本时间统一用前缀范围统计当天。"""
    return f"{today}T00:00:00", f"{today}T23:59:59"


def _medication_status(profile_id: int, today: str) -> tuple[int | None, str | None]:
    """汇总当天用药提醒状态：已确认=1，未完成=0，未设置/待确认=null。"""
    start_at, end_at = _today_bounds(today)
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT reminder_type, title, status, confirmed_at, scheduled_time
            FROM reminders
            WHERE user_profile_id = ?
              AND is_enabled = 1
              AND (reminder_type = 'medication' OR reminder_type = 'medicine' OR title LIKE '%药%')
            """,
            (profile_id,),
        ).fetchall()

    if not rows:
        return None, None

    confirmed_rows = [
        row for row in rows
        if str(row["status"] or "") == "confirmed"
        and (not row["confirmed_at"] or start_at <= str(row["confirmed_at"]) <= end_at)
    ]
    if confirmed_rows:
        confirmed_at = str(confirmed_rows[0]["confirmed_at"] or "")
        medication_time = confirmed_at[11:16] if len(confirmed_at) >= 16 else (str(confirmed_rows[0]["scheduled_time"] or "") or None)
        return 1, medication_time

    if any(str(row["status"] or "") == "missed" for row in rows):
        return 0, None
    return None, None


def _risk_event_count(patient_id: str, today: str) -> int:
    """统计当天 caregiver_events 中的风险事件数量。"""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM caregiver_events
            WHERE patient_id = ?
              AND substr(created_at, 1, 10) = ?
            """,
            (patient_id, today),
        ).fetchone()
    return int(row["count"] or 0) if row else 0


def _conversation_count(profile_id: int, today: str) -> int:
    """统计当天患者侧用户发言次数，作为对话活跃度。"""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM chat_logs
            WHERE user_id = ?
              AND role = 'user'
              AND substr(timestamp, 1, 10) = ?
            """,
            (profile_id, today),
        ).fetchone()
    return int(row["count"] or 0) if row else 0


def _fallback_summary(
    *,
    medication_taken: int | None,
    risk_events: int,
    conversation_count: int,
) -> str:
    """模型不可用时给 prompt 使用的结构化摘要输入，不直接入库。"""
    medication = "已确认用药" if medication_taken == 1 else "未完成用药" if medication_taken == 0 else "用药状态待确认"
    return f"{medication}；风险事件 {risk_events} 次；对话 {conversation_count} 次。"


async def _call_llm_summary(
    *,
    medication_taken: int | None,
    risk_events: int,
    conversation_count: int,
) -> str | None:
    """调用统一 LLM 入口生成 50 字内当日总结；失败返回 None。"""
    prompt = (
        "请根据照护数据生成一句 50 字内中文总结，只输出总结本身。\n"
        f"数据：{_fallback_summary(medication_taken=medication_taken, risk_events=risk_events, conversation_count=conversation_count)}"
    )
    try:
        content = await llm_service.chat(
            system_prompt="你是家庭照护摘要助手，请生成一句简短、客观、温和的中文总结。",
            user_message=prompt,
            max_tokens=80,
        )
        content = re.sub(r"\s+", " ", content).strip("。 ")
        return content[:50] if content else None
    except Exception:
        return None


async def record_today(patient_id: str) -> dict:
    """汇总当日照护数据并 upsert 到 daily_care_summary。"""
    clean_patient_id = str(patient_id or "").strip()
    today = _today_text()
    profile_id = _profile_id_for_patient(clean_patient_id)
    medication_taken, medication_time = _medication_status(profile_id, today)
    risk_events = _risk_event_count(clean_patient_id, today)
    conversation_count = _conversation_count(profile_id, today)
    summary_text = await _call_llm_summary(
        medication_taken=medication_taken,
        risk_events=risk_events,
        conversation_count=conversation_count,
    )

    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO daily_care_summary (
                patient_id, date, medication_taken, medication_time,
                risk_events, conversation_count, mood_score, mood_label, mood_evidence, summary_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(patient_id, date) DO UPDATE SET
                medication_taken = excluded.medication_taken,
                medication_time = excluded.medication_time,
                risk_events = excluded.risk_events,
                conversation_count = excluded.conversation_count,
                mood_score = COALESCE(daily_care_summary.mood_score, excluded.mood_score),
                mood_label = COALESCE(daily_care_summary.mood_label, excluded.mood_label),
                mood_evidence = COALESCE(daily_care_summary.mood_evidence, excluded.mood_evidence),
                summary_text = excluded.summary_text
            """,
            (
                clean_patient_id,
                today,
                medication_taken,
                medication_time,
                risk_events,
                conversation_count,
                None,
                None,
                None,
                summary_text,
            ),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT patient_id, date, medication_taken, medication_time,
                   risk_events, conversation_count, mood_score, mood_label, mood_evidence, summary_text
            FROM daily_care_summary
            WHERE patient_id = ? AND date = ?
            """,
            (clean_patient_id, today),
        ).fetchone()
    return _row_to_dict(row)


async def get_trend(patient_id: str, days: int = 14) -> list[dict]:
    """返回最近 N 天已记录的照护摘要，按日期升序。"""
    clean_patient_id = str(patient_id or "").strip()
    limit = max(1, min(int(days or 14), 90))
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT patient_id, date, medication_taken, medication_time,
                   risk_events, conversation_count, mood_score, mood_label, mood_evidence, summary_text
            FROM daily_care_summary
            WHERE patient_id = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (clean_patient_id, limit),
        ).fetchall()
    return [_row_to_dict(row) for row in reversed(rows)]


def _row_to_dict(row: Any) -> dict:
    """把 SQLite Row 转成 API 友好的结构。"""
    if row is None:
        return {}
    return {
        "patient_id": row["patient_id"],
        "date": row["date"],
        "medication_taken": row["medication_taken"],
        "medication_time": row["medication_time"],
        "risk_events": row["risk_events"],
        "conversation_count": row["conversation_count"],
        "mood_score": row["mood_score"],
        "mood_label": row["mood_label"] if "mood_label" in row.keys() else None,
        "mood_evidence": row["mood_evidence"] if "mood_evidence" in row.keys() else "",
        "evidence": row["mood_evidence"] if "mood_evidence" in row.keys() else "",
        "summary_text": row["summary_text"],
    }
