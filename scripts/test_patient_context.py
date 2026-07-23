"""验证真实患者 prompt 不被 Demo 患者数据污染。

该脚本只构造 prompt，不发真实 LLM 请求。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models.user_profile import UserProfile
from app.services import llm_service, patient_service


def _patient_to_profile(patient: dict) -> UserProfile:
    """把 patients 表记录转换成 prompt 构造所需的轻量 profile。"""
    return UserProfile(
        id=str(patient.get("id") or "") or None,  # type: ignore[arg-type]
        name=str(patient.get("name") or "患者").strip(),
        age=patient.get("age"),
        hometown=str(patient.get("relation") or "").strip(),
        support_mode="alzheimer",
        family_info=str(patient.get("relation") or "").strip(),
        life_events=str(patient.get("notes") or "").strip(),
        preferences=str(patient.get("stage") or "").strip(),
        notes=str(patient.get("notes") or "").strip(),
    )


async def test() -> None:
    patients = await patient_service.list_patients()
    real_patients = [p for p in patients if p["id"] != "demo_patient_001"]

    if not real_patients:
        print("没有真实患者，跳过测试")
        return

    patient = real_patients[0]
    print(f"测试患者: {patient['name']} ({patient['id']})")
    print("检查 prompt 是否有 demo 数据污染...")

    conversation = llm_service.LLMConversationInput(
        system_prompt="请根据当前患者档案和已确认记忆，进行温和、简短的陪伴对话。",
        support_mode="alzheimer",
        profile=_patient_to_profile(patient),
        recent_logs=[],
        user_message="你好，今天想聊一会儿。",
        context_text="",
        memory_summary="",
    )
    resolved = llm_service._resolve_style_context(conversation)  # noqa: SLF001
    prompt = llm_service._build_real_system_prompt(conversation, resolved)  # noqa: SLF001
    user_payload = "\n".join(
        [
            prompt,
            llm_service._profile_text(conversation.profile),  # noqa: SLF001
        ]
    )

    forbidden_terms = ["李桂兰", "小雨", "老王"]
    polluted = [term for term in forbidden_terms if term in user_payload]
    has_real_name = str(patient["name"]) in user_payload

    if polluted:
        print(f"发现 demo 数据污染: {', '.join(polluted)}")
        return
    if not has_real_name:
        print(f"未发现真实患者姓名: {patient['name']}")
        return

    print("无 demo 数据污染")


if __name__ == "__main__":
    asyncio.run(test())
