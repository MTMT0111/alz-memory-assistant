"""Caregiver-reviewed memory capture service."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime
from typing import Any

from app.database import get_connection
from app.models.memory_candidate import (
    MEMORY_CANDIDATE_STATUS,
    MEMORY_CANDIDATE_TYPES,
    MemoryCandidate,
)
from app.services import familiar_material_service


TYPE_LABELS = {
    "old_event": "旧事件",
    "family_photo": "家人照片",
    "familiar_music": "熟悉音乐",
    "old_place": "旧地点",
    "voice_message": "语音留言",
    "daily_object": "日常物品",
    "sensitive_memory": "敏感记忆",
}


def _now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_type(value: Any) -> str:
    text = _clean_text(value)
    return text if text in MEMORY_CANDIDATE_TYPES else "old_event"


def _normalize_status(value: Any) -> str:
    text = _clean_text(value)
    return text if text in MEMORY_CANDIDATE_STATUS else "pending"


def list_candidates(patient_id: int, *, status: str | None = None, limit: int = 100) -> list[MemoryCandidate]:
    """Return memory candidates for one patient."""
    params: list[Any] = [patient_id]
    where = ["patient_id = ?"]
    normalized_status = _normalize_status(status) if status else ""
    if normalized_status:
        where.append("status = ?")
        params.append(normalized_status)
    params.append(max(1, min(limit, 200)))

    with closing(get_connection()) as connection:
        rows = connection.execute(
            f"""
            SELECT * FROM memory_candidates
            WHERE {" AND ".join(where)}
            ORDER BY
                CASE status WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,
                created_at DESC,
                id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
    return [MemoryCandidate.from_row(row) for row in rows]


def get_candidate(patient_id: int, candidate_id: int) -> MemoryCandidate | None:
    """Return one candidate for a patient."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT * FROM memory_candidates
            WHERE patient_id = ? AND id = ?
            """,
            (patient_id, candidate_id),
        ).fetchone()
    return MemoryCandidate.from_row(row) if row else None


def create_candidate(patient_id: int, payload: dict[str, Any]) -> MemoryCandidate:
    """Persist one pending candidate."""
    now = _now_text()
    normalized = {
        "source_message": _clean_text(payload.get("source_message")),
        "suggested_title": _clean_text(payload.get("suggested_title")) or "未命名回忆候选",
        "suggested_description": _clean_text(payload.get("suggested_description")),
        "suggested_material_type": _normalize_type(payload.get("suggested_material_type")),
        "related_person": _clean_text(payload.get("related_person")),
        "sensitivity_level": _clean_text(payload.get("sensitivity_level")) or "low",
        "status": _normalize_status(payload.get("status")),
        "dedup_warning": _clean_text(payload.get("dedup_warning")),
        "conflict_warning": _clean_text(payload.get("conflict_warning")),
    }
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO memory_candidates (
                patient_id, source_message, suggested_title, suggested_description,
                suggested_material_type, related_person, sensitivity_level,
                status, dedup_warning, conflict_warning, created_at, reviewed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                normalized["source_message"],
                normalized["suggested_title"],
                normalized["suggested_description"],
                normalized["suggested_material_type"],
                normalized["related_person"],
                normalized["sensitivity_level"],
                normalized["status"],
                normalized["dedup_warning"],
                normalized["conflict_warning"],
                now,
                "",
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM memory_candidates WHERE id = last_insert_rowid()"
        ).fetchone()
    return MemoryCandidate.from_row(row)


def _find_duplicate(patient_id: int, payload: dict[str, Any]) -> MemoryCandidate | None:
    source_message = _clean_text(payload.get("source_message"))
    suggested_title = _clean_text(payload.get("suggested_title"))
    if not source_message or not suggested_title:
        return None
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT * FROM memory_candidates
            WHERE patient_id = ?
              AND source_message = ?
              AND suggested_title = ?
              AND status = 'pending'
            ORDER BY id DESC
            LIMIT 1
            """,
            (patient_id, source_message, suggested_title),
        ).fetchone()
    return MemoryCandidate.from_row(row) if row else None


def _detect_candidate_payload(message: str) -> dict[str, Any] | None:
    text = _clean_text(message)
    if not text:
        return None

    if any(token in text for token in ("服装厂", "做衣服", "缝纫")):
        return {
            "source_message": text,
            "suggested_title": "服装厂缝纫经历",
            "suggested_description": "李奶奶提到年轻时做衣服，可作为旧经历素材。",
            "suggested_material_type": "old_event",
            "related_person": "",
            "sensitivity_level": "low",
        }
    if any(token in text for token in ("老歌", "听歌", "音乐")):
        return {
            "source_message": text,
            "suggested_title": "熟悉老歌陪伴线索",
            "suggested_description": "李奶奶主动提到老歌，可补充熟悉音乐素材。",
            "suggested_material_type": "familiar_music",
            "related_person": "",
            "sensitivity_level": "low",
        }
    if any(token in text for token in ("菜场", "苹果", "青菜", "温州")):
        return {
            "source_message": text,
            "suggested_title": "温州老城区菜场",
            "suggested_description": "李奶奶提到旧地点或买菜线索，可补充地点回忆素材。",
            "suggested_material_type": "old_place",
            "related_person": "",
            "sensitivity_level": "low",
        }
    if any(token in text for token in ("小雨", "女儿")):
        return {
            "source_message": text,
            "suggested_title": "小雨陪伴线索",
            "suggested_description": "李奶奶主动提到小雨，可补充照片或语音留言素材。",
            "suggested_material_type": "family_photo",
            "related_person": "陈小雨",
            "sensitivity_level": "low",
        }
    if any(token in text for token in ("老王", "王建国", "老伴")):
        return {
            "source_message": text,
            "suggested_title": "老伴王建国相关记忆",
            "suggested_description": "患者提到老伴相关记忆，需由家属审核后再决定是否沉淀。",
            "suggested_material_type": "sensitive_memory",
            "related_person": "王建国",
            "sensitivity_level": "high",
        }
    if any(token in text for token in ("药盒", "钥匙", "杯子")):
        return {
            "source_message": text,
            "suggested_title": "日常物品提示线索",
            "suggested_description": "患者提到常用物品，可补充为日常确认素材。",
            "suggested_material_type": "daily_object",
            "related_person": "",
            "sensitivity_level": "low",
        }
    return None


def capture_candidate_from_message(patient_id: int, message: str) -> MemoryCandidate | None:
    """Create one pending candidate from a suitable user message."""
    payload = _detect_candidate_payload(message)
    if payload is None:
        return None
    duplicate = _find_duplicate(patient_id, payload)
    if duplicate is not None:
        return duplicate
    return create_candidate(patient_id, payload)


def approve_candidate(
    patient_id: int,
    candidate_id: int,
    overrides: dict[str, Any] | None = None,
) -> tuple[MemoryCandidate | None, dict[str, Any] | None]:
    """Approve a candidate and turn it into a familiar material."""
    candidate = get_candidate(patient_id, candidate_id)
    if candidate is None:
        return None, None
    override_payload = overrides or {}
    updated_fields = {
        "suggested_title": _clean_text(override_payload.get("suggested_title")) or candidate.suggested_title,
        "suggested_description": _clean_text(override_payload.get("suggested_description")) or candidate.suggested_description,
        "suggested_material_type": (
            _normalize_type(override_payload.get("suggested_material_type"))
            if override_payload.get("suggested_material_type") is not None
            else candidate.suggested_material_type
        ),
        "related_person": _clean_text(override_payload.get("related_person")) or candidate.related_person,
        "sensitivity_level": _clean_text(override_payload.get("sensitivity_level")) or candidate.sensitivity_level or "low",
    }
    now = _now_text()
    with closing(get_connection()) as connection:
        connection.execute(
            """
            UPDATE memory_candidates
            SET suggested_title = ?,
                suggested_description = ?,
                suggested_material_type = ?,
                related_person = ?,
                sensitivity_level = ?,
                status = 'approved',
                reviewed_at = ?
            WHERE patient_id = ? AND id = ?
            """,
            (
                updated_fields["suggested_title"],
                updated_fields["suggested_description"],
                updated_fields["suggested_material_type"],
                updated_fields["related_person"],
                updated_fields["sensitivity_level"],
                now,
                patient_id,
                candidate_id,
            ),
        )
        connection.commit()
    updated = get_candidate(patient_id, candidate_id)
    material = familiar_material_service.save_material(
        patient_id,
        {
            "material_type": updated.suggested_material_type,
            "title": updated.suggested_title,
            "description": updated.suggested_description,
            "related_person": updated.related_person,
            "sensitivity_level": updated.sensitivity_level,
            "is_sensitive": updated.suggested_material_type == "sensitive_memory" or updated.sensitivity_level in {"medium", "high"},
            "safety_note": "由家属审核后从聊天记录沉淀。",
            "tags": "记忆候选,审核通过",
        },
    )
    return updated, material.to_dict()


def reject_candidate(patient_id: int, candidate_id: int) -> MemoryCandidate | None:
    """Reject one candidate without writing long-term memory."""
    candidate = get_candidate(patient_id, candidate_id)
    if candidate is None:
        return None
    now = _now_text()
    with closing(get_connection()) as connection:
        connection.execute(
            """
            UPDATE memory_candidates
            SET status = 'rejected', reviewed_at = ?
            WHERE patient_id = ? AND id = ?
            """,
            (now, patient_id, candidate_id),
        )
        connection.commit()
    return get_candidate(patient_id, candidate_id)


def clear_candidates(patient_id: int) -> int:
    """Remove stored candidates for deterministic demos/tests."""
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "DELETE FROM memory_candidates WHERE patient_id = ?",
            (patient_id,),
        )
        connection.commit()
    return int(cursor.rowcount or 0)
