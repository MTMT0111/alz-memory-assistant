#!/usr/bin/env python3
"""Smoke test caregiver-reviewed memory capture and approval flow."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_local_env_file

load_local_env_file()

from app.services import chat_service, familiar_material_service, memory_candidate_service, profile_service


def main() -> int:
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    patient_id = profile.id or 0
    if not patient_id:
        print("FAIL: missing demo patient id")
        return 1

    memory_candidate_service.clear_candidates(patient_id)
    materials_before = familiar_material_service.list_materials(patient_id)
    count_before = len(materials_before)

    chat_service.generate_chat_reply(
        user_id=patient_id,
        message="我以前是不是在服装厂做过衣服？",
    )
    candidates = memory_candidate_service.list_candidates(patient_id, status="pending")
    if not candidates:
        print("FAIL: no memory candidate generated from reminiscence message")
        return 1

    candidate = candidates[0]
    if candidate.suggested_material_type != "old_event":
        print(f"FAIL: expected old_event candidate, got {candidate.suggested_material_type}")
        return 1

    approved, material = memory_candidate_service.approve_candidate(patient_id, candidate.id or 0)
    if approved is None or approved.status != "approved":
        print("FAIL: candidate approval failed")
        return 1
    materials_after = familiar_material_service.list_materials(patient_id)
    if len(materials_after) <= count_before:
        print("FAIL: familiar material was not created on approval")
        return 1

    rejected = memory_candidate_service.create_candidate(
        patient_id,
        {
            "source_message": "老王怎么还没回来？",
            "suggested_title": "老伴王建国相关记忆",
            "suggested_description": "敏感内容需要家属审核。",
            "suggested_material_type": "sensitive_memory",
            "related_person": "王建国",
            "sensitivity_level": "high",
        },
    )
    rejected = memory_candidate_service.reject_candidate(patient_id, rejected.id or 0)
    if rejected is None or rejected.status != "rejected":
        print("FAIL: candidate rejection failed")
        return 1

    print("PASS: memory candidate review flow works.")
    print(f"approved candidate: {approved.to_dict()}")
    print(f"created material: {material}")
    print(f"rejected candidate: {rejected.to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
