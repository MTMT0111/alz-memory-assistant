#!/usr/bin/env python3
"""Verify chat diagnostics expose matched familiar materials."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_local_env_file

load_local_env_file()

from app.services import chat_service


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


def _run_message(patient_id: int, message: str, expected_type: str) -> None:
    result = chat_service.generate_chat_reply(user_id=patient_id, message=message)
    diagnostics = result.get("diagnostics") or {}
    materials = diagnostics.get("materials_used") or []
    material_types = {item.get("material_type") for item in materials}
    print(f"message={message}")
    print(f"actual_provider={diagnostics.get('actual_provider')} fallback={diagnostics.get('fallback_used')}")
    print(f"materials_used={materials}")
    _assert(materials, f"materials_used is empty for: {message}")
    _assert(expected_type in material_types, f"expected {expected_type}, got {material_types}")
    _assert(diagnostics.get("context_items_count", 0) > 0, "context_items_count missing")
    _assert(diagnostics.get("history_turns_used", 0) >= 1, "history_turns_used missing")


def main() -> int:
    print("Chat context materials smoke test")
    profile = seed_demo_patient()
    patient_id = profile.id
    _assert(patient_id is not None, "demo patient id is missing")

    _run_message(patient_id, "我想听老歌", "familiar_music")
    _run_message(patient_id, "小雨什么时候回来？", "voice_message")
    _run_message(patient_id, "我以前是不是在服装厂做过衣服？", "old_event")

    print("PASS: chat diagnostics show relevant familiar materials.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
