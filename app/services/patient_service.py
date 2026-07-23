"""多患者档案管理服务。

这里维护照护者选择患者所需的轻量档案，不存真实照片，只用 emoji 做快速识别。
"""

from __future__ import annotations

from contextlib import closing
from datetime import date, datetime
import uuid
from typing import Any

from app.database import get_connection


ALLOWED_UPDATE_FIELDS = {"name", "age", "relation", "avatar_emoji", "stage", "notes"}
VALID_STAGES = {"轻度", "中度", "重度"}
MOOD_EMOJI = {
    "低落": "😔",
    "焦虑": "😟",
    "困惑": "😕",
    "平稳": "😐",
    "愉快": "😊",
    "未知": "—",
}


def _row_to_patient(row: Any) -> dict:
    """把 SQLite Row 转成前端/API 使用的患者字典。"""
    return {
        "id": row["id"],
        "name": row["name"],
        "age": row["age"],
        "relation": row["relation"] or "",
        "avatar_emoji": row["avatar_emoji"] or "👵",
        "stage": row["stage"] or "轻度",
        "notes": row["notes"] or "",
        "created_at": row["created_at"] or "",
        "is_active": bool(row["is_active"]),
    }


def _table_exists(connection, table_name: str) -> bool:
    """检查可选表是否存在，兼容旧数据库。"""
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)


def _column_names(connection, table_name: str) -> set[str]:
    """读取表字段名，避免不同历史版本字段不一致时崩溃。"""
    return {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _days_since_last_conversation(connection, patient_id: str) -> int | None:
    """统计最近一次会话距今天数。"""
    row = connection.execute(
        """
        SELECT MAX(timestamp) AS last_time
        FROM conversations
        WHERE patient_id = ?
        """,
        (patient_id,),
    ).fetchone()
    last_time = str(row["last_time"] or "").strip() if row else ""
    if not last_time:
        return None
    try:
        last_date = datetime.fromisoformat(last_time.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            last_date = datetime.strptime(last_time[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return max(0, (date.today() - last_date).days)


def _memory_count(connection, patient_id: str) -> int:
    """统计已审批记忆数量；优先 approved_memories，回退到已通过候选。"""
    if _table_exists(connection, "approved_memories"):
        columns = _column_names(connection, "approved_memories")
        patient_column = "patient_id" if "patient_id" in columns else "user_profile_id" if "user_profile_id" in columns else ""
        if patient_column:
            status_sql = ""
            params: list[Any] = [patient_id]
            if "approved" in columns:
                status_sql = " AND (approved = 1 OR lower(CAST(approved AS TEXT)) = 'true' OR lower(CAST(approved AS TEXT)) = 'approved')"
            elif "is_approved" in columns:
                status_sql = " AND (is_approved = 1 OR lower(CAST(is_approved AS TEXT)) = 'true' OR lower(CAST(is_approved AS TEXT)) = 'approved')"
            elif "status" in columns:
                status_sql = " AND status = 'approved'"
            row = connection.execute(
                f"SELECT COUNT(*) AS count FROM approved_memories WHERE {patient_column} = ?{status_sql}",
                params,
            ).fetchone()
            return int(row["count"] or 0) if row else 0

    if _table_exists(connection, "memory_candidates"):
        columns = _column_names(connection, "memory_candidates")
        if "patient_id" in columns and "status" in columns:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM memory_candidates WHERE CAST(patient_id AS TEXT) = ? AND status = 'approved'",
                (patient_id,),
            ).fetchone()
            return int(row["count"] or 0) if row else 0
    return 0


def _today_mood_emoji(connection, patient_id: str) -> str:
    """读取今日情绪标签并映射成卡片 emoji。"""
    row = connection.execute(
        """
        SELECT mood_label
        FROM daily_care_summary
        WHERE patient_id = ? AND date = ?
        """,
        (patient_id, date.today().isoformat()),
    ).fetchone()
    label = str(row["mood_label"] or "未知").strip() if row else "未知"
    return MOOD_EMOJI.get(label, "—")


def _augment_patient(patient: dict) -> dict:
    """补充患者卡片所需统计信息。"""
    patient_id = str(patient.get("id") or "")
    with closing(get_connection()) as connection:
        patient["last_conversation_days"] = _days_since_last_conversation(connection, patient_id)
        patient["memory_count"] = _memory_count(connection, patient_id)
        patient["today_mood_emoji"] = _today_mood_emoji(connection, patient_id)
    return patient


def _clean_stage(stage: str | None) -> str:
    """限制病情阶段为固定选项，避免页面出现脏值。"""
    clean_stage = str(stage or "轻度").strip()
    return clean_stage if clean_stage in VALID_STAGES else "轻度"


async def list_patients() -> list[dict]:
    """返回所有启用患者，按创建时间倒序。"""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, name, age, relation, avatar_emoji, stage, notes, created_at, is_active
            FROM patients
            WHERE is_active = 1
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return [_augment_patient(_row_to_patient(row)) for row in rows]


async def get_patient(patient_id: str) -> dict | None:
    """读取单个启用患者；不存在或已停用时返回 None。"""
    clean_id = str(patient_id or "").strip()
    if not clean_id:
        return None
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT id, name, age, relation, avatar_emoji, stage, notes, created_at, is_active
            FROM patients
            WHERE id = ? AND is_active = 1
            """,
            (clean_id,),
        ).fetchone()
    return _augment_patient(_row_to_patient(row)) if row else None


async def create_patient(
    name: str,
    age: int | None,
    relation: str,
    stage: str,
    notes: str,
    avatar_emoji: str = "👵",
) -> str:
    """创建患者档案，返回 UUID。"""
    clean_name = str(name or "").strip()
    if not clean_name:
        raise ValueError("name is required")

    patient_id = str(uuid.uuid4())
    clean_age = int(age) if age not in (None, "") else None
    clean_avatar = str(avatar_emoji or "👵").strip() or "👵"
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO patients (id, name, age, relation, stage, notes, avatar_emoji, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                patient_id,
                clean_name,
                clean_age,
                str(relation or "").strip(),
                _clean_stage(stage),
                str(notes or "").strip(),
                clean_avatar,
            ),
        )
        connection.commit()
    return patient_id


async def update_patient(patient_id: str, **kwargs) -> None:
    """只更新调用方显式传入的允许字段。"""
    clean_id = str(patient_id or "").strip()
    updates: dict[str, Any] = {}
    for key, value in kwargs.items():
        if key not in ALLOWED_UPDATE_FIELDS or value is None:
            continue
        if key == "stage":
            updates[key] = _clean_stage(str(value))
        elif key == "age":
            updates[key] = int(value) if value not in ("", None) else None
        else:
            updates[key] = str(value).strip()

    if not clean_id or not updates:
        return

    assignments = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [clean_id]
    with closing(get_connection()) as connection:
        connection.execute(
            f"UPDATE patients SET {assignments} WHERE id = ?",
            values,
        )
        connection.commit()


async def deactivate_patient(patient_id: str) -> None:
    """软删除患者档案，保留历史照护数据。"""
    clean_id = str(patient_id or "").strip()
    if not clean_id:
        return
    with closing(get_connection()) as connection:
        connection.execute(
            "UPDATE patients SET is_active = 0 WHERE id = ?",
            (clean_id,),
        )
        connection.commit()
