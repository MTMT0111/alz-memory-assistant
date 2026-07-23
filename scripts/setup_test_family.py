"""为真实/模拟照护家庭初始化一组可试用账号和患者数据。"""

from __future__ import annotations

import asyncio
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sys
import uuid


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import get_connection
from app.init_db import initialize_database
from app.services import auth_service


def _clean_pin(value: str, fallback: str) -> str:
    """保证 PIN 为 4 位数字，不符合时使用默认值。"""
    clean_value = str(value or "").strip()
    return clean_value if len(clean_value) == 4 and clean_value.isdigit() else fallback


async def setup() -> None:
    """
    为一个测试家庭创建初始数据：
    - 1个患者档案
    - 1个主照护者账号（PIN: 1234）
    - 1个协作照护者账号（PIN: 5678）
    - 完成知情同意记录
    - 创建2条用药提醒（早8点/晚8点）
    """
    initialize_database()

    patient_id = str(uuid.uuid4())
    patient_name = input("患者姓名（如：奶奶）: ").strip() or "测试患者"
    patient_age_text = input("患者年龄（如：78）: ").strip() or "75"
    try:
        patient_age = int(patient_age_text)
    except ValueError:
        patient_age = 75

    owner_name = input("主照护者姓名（如：小明）: ").strip() or "主照护者"
    owner_pin = _clean_pin(input("主照护者 PIN（4位数字，默认1234）: ").strip(), "1234")

    member_name = input("协作照护者姓名（如：小红，默认协作照护者）: ").strip() or "协作照护者"
    member_pin = _clean_pin(input("协作照护者 PIN（4位数字，默认5678）: ").strip(), "5678")

    owner_id = str(uuid.uuid4())
    member_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")

    with closing(get_connection()) as connection:
        connection.execute(
            """
            INSERT INTO patients (id, name, age, relation, avatar_emoji, stage, notes, is_active)
            VALUES (?, ?, ?, ?, '👵', '中度', '测试家庭初始化档案', 1)
            """,
            (patient_id, patient_name, patient_age, "家人"),
        )
        connection.execute(
            """
            INSERT INTO caregivers (id, name, pin_hash, role, avatar_emoji, is_active)
            VALUES (?, ?, ?, 'owner', '👤', 1)
            """,
            (owner_id, owner_name, auth_service.hash_pin(owner_pin)),
        )
        connection.execute(
            """
            INSERT INTO caregivers (id, name, pin_hash, role, avatar_emoji, is_active)
            VALUES (?, ?, ?, 'member', '👤', 1)
            """,
            (member_id, member_name, auth_service.hash_pin(member_pin)),
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO caregiver_patient_access (caregiver_id, patient_id)
            VALUES (?, ?)
            """,
            [(owner_id, patient_id), (member_id, patient_id), ("default_caregiver", patient_id)],
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO consent_records (
                patient_id, consented_by, consent_time, consent_version, ip_address
            )
            VALUES (?, ?, ?, 'v1.0', 'setup_test_family')
            """,
            (patient_id, owner_name, now),
        )
        connection.executemany(
            """
            INSERT INTO medication_schedule (
                patient_id, medication_name, remind_time, dose, enabled
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            [
                (patient_id, "晨间用药", "08:00", "按医嘱"),
                (patient_id, "晚间用药", "20:00", "按医嘱"),
            ],
        )
        connection.commit()

    print("\n=== 初始化完成 ===")
    print(f"患者 ID: {patient_id}")
    print(f"患者姓名: {patient_name}")
    print(f"主照护者: {owner_name}，PIN: {owner_pin}")
    print(f"协作照护者: {member_name}，PIN: {member_pin}")
    print("访问地址: http://localhost:8000/login")
    print(f"照护看板: http://localhost:8000/care-portal/{patient_id}")
    print(f"患者对话: http://localhost:8000/conversation/{patient_id}")


if __name__ == "__main__":
    asyncio.run(setup())
