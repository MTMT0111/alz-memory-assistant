#!/usr/bin/env python3
"""Smoke test familiar materials seed data and CRUD API."""

from __future__ import annotations

import sys
import importlib.util
import asyncio
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_local_env_file

load_local_env_file()

from app.main import (
    FamiliarMaterialRequest,
    create_familiar_material,
    delete_familiar_material,
    get_familiar_materials,
    update_familiar_material,
)
from app.services import familiar_material_service


def _load_seed_demo_patient():
    module_path = PROJECT_ROOT / "scripts" / "seed_demo_patient.py"
    spec = importlib.util.spec_from_file_location("project_seed_demo_patient", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/seed_demo_patient.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.seed_demo_patient


seed_demo_patient = _load_seed_demo_patient()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def _run_api_checks(patient_id: int, payload: dict) -> None:
    data = await get_familiar_materials(patient_id)
    _assert(len(data.get("materials", [])) >= 6, "GET materials returned too few seeded items")
    _assert(data.get("status", {}).get("family_photo") is True, "family_photo status should be configured")
    _assert(data.get("status", {}).get("sensitive_count", 0) >= 1, "sensitive material status missing")

    created_response = await create_familiar_material(patient_id, FamiliarMaterialRequest(**payload))
    created = created_response.get("material") or {}
    material_id = created.get("id")
    _assert(material_id, "POST material did not return an id")
    _assert(created.get("title") == payload["title"], "created material title mismatch")

    update_payload = {**payload, "title": f"{payload['title']} 已更新", "is_sensitive": True, "safety_note": "仅在用户主动提及时使用。"}
    updated_response = await update_familiar_material(
        patient_id,
        material_id,
        FamiliarMaterialRequest(**update_payload),
    )
    updated = updated_response.get("material") or {}
    _assert(updated.get("title") == update_payload["title"], "updated material title mismatch")
    _assert(updated.get("is_sensitive") is True, "updated material sensitivity mismatch")

    deleted_response = await delete_familiar_material(patient_id, material_id)
    remaining_ids = {item.get("id") for item in deleted_response.get("materials", [])}
    _assert(material_id not in remaining_ids, "deleted material still appears in list")


def main() -> int:
    print("Familiar materials module smoke test")
    profile = seed_demo_patient()
    patient_id = profile.id
    _assert(patient_id is not None, "demo patient id is missing")

    seeded = familiar_material_service.list_materials(patient_id)
    titles = {item.title for item in seeded}
    expected_titles = {
        "女儿小雨照片",
        "小雨晚间安抚留言",
        "轻柔老歌播放清单",
        "温州老城区菜场",
        "服装厂缝纫经历",
        "老伴王建国",
    }
    _assert(expected_titles.issubset(titles), "demo familiar materials were not fully seeded")

    test_title = f"测试旧地点 {uuid4().hex[:8]}"
    payload = {
        "material_type": "daily_object",
        "title": test_title,
        "description": "接口测试用日常物品，会在脚本结束时删除。",
        "related_person": "测试家属",
        "file_path": "https://example.com/place.jpg",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "transcript_text": "这是一条测试文字。",
        "use_scene": "reminiscence",
        "tags": "测试,日常物品",
        "safety_note": "",
        "is_sensitive": False,
        "is_active": True,
    }

    asyncio.run(_run_api_checks(patient_id, payload))

    print("PASS: familiar materials seed data and API CRUD are working.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
