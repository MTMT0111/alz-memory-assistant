"""用药时间表与前端轮询提醒服务。"""

from __future__ import annotations

from contextlib import closing
from datetime import date, datetime
import re
from typing import Any

from app.database import get_connection


TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _today_text() -> str:
    """返回今天日期，用于 daily_care_summary 的唯一键。"""
    return date.today().isoformat()


def _now_time_text() -> str:
    """返回当前 HH:MM，记录实际服药时间。"""
    return datetime.now().strftime("%H:%M")


def _clean_time(value: str) -> str:
    """校验 HH:MM 时间格式，避免错误数据进入轮询逻辑。"""
    clean_value = str(value or "").strip()
    if not TIME_RE.match(clean_value):
        raise ValueError("remind_time must be HH:MM")
    return clean_value


def _daily_medication_notified(patient_id: str, today: str) -> bool:
    """根据当日汇总表判断今天是否已经记录过服药。"""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT medication_taken
            FROM daily_care_summary
            WHERE patient_id = ? AND date = ?
            """,
            (patient_id, today),
        ).fetchone()
    return bool(row and row["medication_taken"] == 1)


def _row_to_schedule(row: Any, *, notified: bool) -> dict:
    """把 SQLite Row 转成前端提醒列表使用的结构。"""
    return {
        "id": row["id"],
        "medication_name": row["medication_name"],
        "remind_time": row["remind_time"],
        "dose": row["dose"] or "",
        "enabled": bool(row["enabled"]),
        "notified": bool(notified),
    }


async def get_today_schedules(patient_id: str) -> list[dict]:
    """返回该患者今日启用的用药提醒，按提醒时间排序。"""
    clean_patient_id = str(patient_id or "").strip()
    if not clean_patient_id:
        return []

    today = _today_text()
    notified = _daily_medication_notified(clean_patient_id, today)
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, medication_name, remind_time, dose, enabled
            FROM medication_schedule
            WHERE patient_id = ? AND enabled = 1
            ORDER BY remind_time ASC, id ASC
            """,
            (clean_patient_id,),
        ).fetchall()
    return [_row_to_schedule(row, notified=notified) for row in rows]


async def list_schedules(patient_id: str) -> list[dict]:
    """返回设置页展示的全部用药提醒，包含暂停项。"""
    clean_patient_id = str(patient_id or "").strip()
    if not clean_patient_id:
        return []

    today = _today_text()
    notified = _daily_medication_notified(clean_patient_id, today)
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, medication_name, remind_time, dose, enabled
            FROM medication_schedule
            WHERE patient_id = ?
            ORDER BY remind_time ASC, id ASC
            """,
            (clean_patient_id,),
        ).fetchall()
    return [_row_to_schedule(row, notified=notified) for row in rows]


async def add_schedule(patient_id: str, medication_name: str, remind_time: str, dose: str) -> int:
    """新增一条用药提醒时间，返回新记录 id。"""
    clean_patient_id = str(patient_id or "").strip()
    clean_name = str(medication_name or "").strip()
    clean_time = _clean_time(remind_time)
    clean_dose = str(dose or "").strip()
    if not clean_patient_id:
        raise ValueError("patient_id is required")
    if not clean_name:
        raise ValueError("medication_name is required")

    with closing(get_connection()) as connection:
        cursor = connection.execute(
            """
            INSERT INTO medication_schedule (patient_id, medication_name, remind_time, dose, enabled)
            VALUES (?, ?, ?, ?, 1)
            """,
            (clean_patient_id, clean_name, clean_time, clean_dose),
        )
        connection.commit()
        return int(cursor.lastrowid)


async def toggle_schedule(schedule_id: int, enabled: bool) -> None:
    """启用或暂停一条用药提醒。"""
    with closing(get_connection()) as connection:
        connection.execute(
            """
            UPDATE medication_schedule
            SET enabled = ?
            WHERE id = ?
            """,
            (1 if enabled else 0, int(schedule_id)),
        )
        connection.commit()


async def delete_schedule(schedule_id: int) -> None:
    """删除一条用药提醒设置。"""
    with closing(get_connection()) as connection:
        connection.execute(
            "DELETE FROM medication_schedule WHERE id = ?",
            (int(schedule_id),),
        )
        connection.commit()


async def record_taken(patient_id: str, schedule_id: int) -> None:
    """记录今日已服药，供提醒横幅的“已服药”按钮调用。"""
    clean_patient_id = str(patient_id or "").strip()
    if not clean_patient_id:
        raise ValueError("patient_id is required")

    try:
        clean_schedule_id = int(schedule_id)
    except (TypeError, ValueError):
        clean_schedule_id = 0

    today = _today_text()
    medication_time = _now_time_text()
    with closing(get_connection()) as connection:
        if clean_schedule_id:
            schedule = connection.execute(
                """
                SELECT id
                FROM medication_schedule
                WHERE id = ? AND patient_id = ?
                """,
                (clean_schedule_id, clean_patient_id),
            ).fetchone()
            if schedule is None:
                raise ValueError("schedule not found")
        connection.execute(
            """
            INSERT INTO daily_care_summary (
                patient_id, date, medication_taken, medication_time
            )
            VALUES (?, ?, 1, ?)
            ON CONFLICT(patient_id, date) DO UPDATE SET
                medication_taken = 1,
                medication_time = excluded.medication_time
            """,
            (clean_patient_id, today, medication_time),
        )
        connection.commit()


async def record_medication_taken(patient_id: str) -> dict:
    """兼容旧调用：记录今日已服药并返回写入结果。"""
    await record_taken(patient_id, 0)
    return {
        "patient_id": str(patient_id or "").strip(),
        "date": _today_text(),
        "medication_taken": 1,
        "medication_time": _now_time_text(),
    }
