"""知情同意记录服务。

同意记录只追加不修改；重复提交同一 patient_id/version 时保持原记录不变。
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime
from typing import Any

from app.database import get_connection


DEFAULT_CONSENT_VERSION = "v1.0"


def _now_text() -> str:
    """记录本地时间，便于家属端审计。"""
    return datetime.now().isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    """清理表单输入，避免写入空白字符串。"""
    return str(value or "").strip()


def get_consent(patient_id: str, consent_version: str = DEFAULT_CONSENT_VERSION) -> dict[str, Any]:
    """查询某患者在指定版本下是否已有有效同意记录。"""
    clean_patient_id = _clean_text(patient_id)
    clean_version = _clean_text(consent_version) or DEFAULT_CONSENT_VERSION
    if not clean_patient_id:
        return {"consented": False, "consent_time": ""}

    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT consent_time, consented_by, consent_version
            FROM consent_records
            WHERE patient_id = ? AND consent_version = ?
            LIMIT 1
            """,
            (clean_patient_id, clean_version),
        ).fetchone()

    if row is None:
        return {"consented": False, "consent_time": ""}
    return {
        "consented": True,
        "consent_time": row["consent_time"] or "",
        "consented_by": row["consented_by"] or "",
        "consent_version": row["consent_version"] or clean_version,
    }


def has_consent(patient_id: str, consent_version: str = DEFAULT_CONSENT_VERSION) -> bool:
    """返回是否已经完成知情同意。"""
    return bool(get_consent(patient_id, consent_version).get("consented"))


def record_consent(
    *,
    patient_id: str,
    consented_by: str,
    consent_version: str = DEFAULT_CONSENT_VERSION,
    ip_address: str = "",
) -> dict[str, Any]:
    """写入知情同意记录；已有记录时不更新原记录。"""
    clean_patient_id = _clean_text(patient_id)
    clean_consented_by = _clean_text(consented_by)
    clean_version = _clean_text(consent_version) or DEFAULT_CONSENT_VERSION
    if not clean_patient_id:
        raise ValueError("patient_id is required")
    if not clean_consented_by:
        raise ValueError("consented_by is required")

    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO consent_records (
                patient_id, consented_by, consent_time, consent_version, ip_address
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                clean_patient_id,
                clean_consented_by,
                _now_text(),
                clean_version,
                _clean_text(ip_address),
            ),
        )
        connection.commit()

    return {"ok": True}
