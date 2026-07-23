"""照护者 PIN 登录与患者访问控制服务。"""

from __future__ import annotations

from contextlib import closing
import hashlib
import os
import re
import secrets
import uuid
from typing import Any

from app.config import ENV_PATH, load_local_env_file
from app.database import get_connection

try:
    from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
except Exception:  # pragma: no cover - 本地未安装时保持应用可导入
    BadSignature = SignatureExpired = URLSafeTimedSerializer = None  # type: ignore[assignment]


load_local_env_file()

TOKEN_SALT = "alz-caregiver-auth"
TOKEN_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
PIN_RE = re.compile(r"^\d{4}$")
VALID_ROLES = {"owner", "member"}


def _clean_text(value: Any) -> str:
    """清理输入文本，避免空白值进入数据库。"""
    return str(value or "").strip()


def _is_placeholder(value: str) -> bool:
    """把示例占位值当成未配置。"""
    lower_value = value.lower()
    return (not value) or "your_" in lower_value or "_here" in lower_value


def _append_env_line(key: str, value: str) -> None:
    """把新生成的密钥追加到 .env，便于下次启动继续复用。"""
    try:
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        ENV_PATH.write_text(f"{existing}{prefix}{key}={value}\n", encoding="utf-8")
    except OSError:
        # 写 .env 失败时不阻断登录，当前进程仍会保留该密钥。
        return


def _get_secret_key() -> str:
    """读取 AUTH_SECRET_KEY；缺失时自动生成并回写 .env。"""
    current = _clean_text(os.getenv("AUTH_SECRET_KEY"))
    if current and not _is_placeholder(current):
        return current

    secret_key = secrets.token_hex(32)
    os.environ["AUTH_SECRET_KEY"] = secret_key
    _append_env_line("AUTH_SECRET_KEY", secret_key)
    return secret_key


def _get_serializer():
    """惰性创建 itsdangerous serializer，避免依赖缺失时导入直接失败。"""
    if URLSafeTimedSerializer is None:
        raise RuntimeError("itsdangerous 未安装，请先执行 pip install itsdangerous")
    return URLSafeTimedSerializer(_get_secret_key(), salt=TOKEN_SALT)


def _validate_pin(pin: str) -> str:
    """限制 PIN 为四位数字，适合家庭内部简单认证。"""
    clean_pin = _clean_text(pin)
    if not PIN_RE.match(clean_pin):
        raise ValueError("PIN 码必须是 4 位数字")
    return clean_pin


def _row_to_caregiver(row: Any) -> dict[str, Any]:
    """把数据库行转成前端可直接使用的照护者对象。"""
    return {
        "id": row["id"],
        "name": row["name"],
        "role": row["role"] or "member",
        "avatar_emoji": row["avatar_emoji"] or "👤",
        "created_at": row["created_at"] or "",
        "is_active": bool(row["is_active"]),
    }


def hash_pin(pin: str) -> str:
    """把 PIN 转成 SHA256 hash，数据库不保存明文。"""
    clean_pin = _validate_pin(pin)
    return hashlib.sha256(clean_pin.encode("utf-8")).hexdigest()


def create_token(caregiver_id: str) -> str:
    """签发照护者登录 token。"""
    serializer = _get_serializer()
    return str(serializer.dumps({"caregiver_id": _clean_text(caregiver_id)}))


def verify_token(token: str) -> str | None:
    """验证登录 token，过期或无效时返回 None。"""
    clean_token = _clean_text(token)
    if not clean_token:
        return None
    try:
        serializer = _get_serializer()
        payload = serializer.loads(clean_token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired, RuntimeError, TypeError, ValueError):
        return None
    if isinstance(payload, dict):
        caregiver_id = _clean_text(payload.get("caregiver_id"))
        return caregiver_id or None
    return None


async def get_caregiver(caregiver_id: str) -> dict[str, Any] | None:
    """读取一位启用中的照护者。"""
    clean_id = _clean_text(caregiver_id)
    if not clean_id:
        return None
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT id, name, role, avatar_emoji, created_at, is_active
            FROM caregivers
            WHERE id = ? AND is_active = 1
            """,
            (clean_id,),
        ).fetchone()
    return _row_to_caregiver(row) if row else None


async def list_caregivers() -> list[dict[str, Any]]:
    """返回所有启用中的照护者。"""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, name, role, avatar_emoji, created_at, is_active
            FROM caregivers
            WHERE is_active = 1
            ORDER BY
                CASE WHEN role = 'owner' THEN 0 ELSE 1 END,
                created_at ASC,
                id ASC
            """
        ).fetchall()
    return [_row_to_caregiver(row) for row in rows]


async def verify_pin(caregiver_id: str, pin: str) -> bool:
    """校验照护者输入的 PIN 是否正确。"""
    clean_id = _clean_text(caregiver_id)
    clean_pin = _clean_text(pin)
    if not clean_id or not clean_pin:
        return False
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT pin_hash
            FROM caregivers
            WHERE id = ? AND is_active = 1
            """,
            (clean_id,),
        ).fetchone()
    if row is None:
        return False
    try:
        return str(row["pin_hash"] or "") == hash_pin(clean_pin)
    except ValueError:
        return False


async def grant_patient_access(caregiver_id: str, patient_id: str) -> None:
    """给照护者授予某位患者的协作访问权限。"""
    clean_caregiver_id = _clean_text(caregiver_id)
    clean_patient_id = _clean_text(patient_id)
    if not clean_caregiver_id or not clean_patient_id:
        return
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO caregiver_patient_access (caregiver_id, patient_id)
            VALUES (?, ?)
            """,
            (clean_caregiver_id, clean_patient_id),
        )
        connection.commit()


async def list_accessible_patient_ids(caregiver_id: str) -> list[str]:
    """列出某位照护者当前可访问的患者 id。"""
    caregiver = await get_caregiver(caregiver_id)
    if not caregiver:
        return []
    if caregiver.get("role") == "owner":
        with closing(get_connection()) as connection:
            rows = connection.execute(
                "SELECT id FROM patients WHERE is_active = 1 ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [str(row["id"]) for row in rows]

    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT patient_id
            FROM caregiver_patient_access
            WHERE caregiver_id = ?
            ORDER BY granted_at ASC, patient_id ASC
            """,
            (_clean_text(caregiver_id),),
        ).fetchall()
    return [str(row["patient_id"]) for row in rows]


async def check_access(caregiver_id: str, patient_id: str) -> bool:
    """检查照护者是否有权访问某位患者。owner 默认可访问全部。"""
    clean_patient_id = _clean_text(patient_id)
    if not clean_patient_id:
        return False
    caregiver = await get_caregiver(caregiver_id)
    if not caregiver:
        return False
    if caregiver.get("role") == "owner":
        return True
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM caregiver_patient_access
            WHERE caregiver_id = ? AND patient_id = ?
            LIMIT 1
            """,
            (_clean_text(caregiver_id), clean_patient_id),
        ).fetchone()
    return bool(row)


async def create_caregiver(
    name: str,
    pin: str,
    role: str = "member",
    avatar_emoji: str = "👤",
    patient_id: str | None = None,
) -> dict[str, Any]:
    """新增一位照护者，并可选授予当前患者访问权限。"""
    clean_name = _clean_text(name)
    clean_role = _clean_text(role) or "member"
    clean_avatar = _clean_text(avatar_emoji) or "👤"
    if not clean_name:
        raise ValueError("name is required")
    if clean_role not in VALID_ROLES:
        raise ValueError("role must be owner or member")

    caregiver_id = str(uuid.uuid4())
    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO caregivers (id, name, pin_hash, role, avatar_emoji, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (caregiver_id, clean_name, hash_pin(pin), clean_role, clean_avatar),
        )
        if patient_id:
            connection.execute(
                """
                INSERT OR IGNORE INTO caregiver_patient_access (caregiver_id, patient_id)
                VALUES (?, ?)
                """,
                (caregiver_id, _clean_text(patient_id)),
            )
        connection.commit()
    created = await get_caregiver(caregiver_id)
    if created is None:
        raise ValueError("caregiver create failed")
    return created


async def update_pin(caregiver_id: str, new_pin: str) -> None:
    """更新某位照护者的 PIN hash。"""
    clean_id = _clean_text(caregiver_id)
    if not clean_id:
        raise ValueError("caregiver_id is required")
    with closing(get_connection()) as connection:
        connection.execute(
            """
            UPDATE caregivers
            SET pin_hash = ?
            WHERE id = ? AND is_active = 1
            """,
            (hash_pin(new_pin), clean_id),
        )
        connection.commit()


async def deactivate_caregiver(caregiver_id: str) -> None:
    """软删除照护者，保留历史协作关系。"""
    clean_id = _clean_text(caregiver_id)
    if not clean_id:
        raise ValueError("caregiver_id is required")
    if clean_id == "default_caregiver":
        raise ValueError("默认主照护者不能停用")
    with closing(get_connection()) as connection:
        connection.execute(
            "UPDATE caregivers SET is_active = 0 WHERE id = ?",
            (clean_id,),
        )
        connection.commit()


async def get_schedule_patient_id(schedule_id: int) -> str | None:
    """通过提醒 id 反查患者 id，用于路由权限判断。"""
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT patient_id FROM medication_schedule WHERE id = ?",
            (int(schedule_id),),
        ).fetchone()
    return _clean_text(row["patient_id"]) if row else None


async def get_risk_event_patient_id(event_id: int) -> str | None:
    """通过风险事件 id 反查患者 id，用于处理权限。"""
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT patient_id FROM risk_events WHERE id = ?",
            (int(event_id),),
        ).fetchone()
    return _clean_text(row["patient_id"]) if row else None
