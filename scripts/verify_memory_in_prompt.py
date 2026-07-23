#!/usr/bin/env python3
"""验证语义记忆是否进入 LLM prompt，不发送真实 LLM 请求。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.models.user_profile import UserProfile
from app.services import llm_service, memory_vector_service


MOCK_PATIENT_ID = "patient_001"
MOCK_QUERY = "妈妈年轻时喜欢什么"


MOCK_MEMORIES = [
    {"memory_id": "m1", "text": "妈妈年轻时在服装厂做缝纫，手很巧。", "score": 0.93},
    {"memory_id": "m2", "text": "妈妈喜欢听老歌，下午听会更安心。", "score": 0.91},
    {"memory_id": "m3", "text": "妈妈以前常去温州老城区菜场买苹果。", "score": 0.88},
    {"memory_id": "m4", "text": "妈妈提到女儿小雨晚上八点会联系她。", "score": 0.86},
    {"memory_id": "m5", "text": "这条是第 5 条，若出现在 prompt 中说明没有限制 top-4。", "score": 0.70},
    {"memory_id": "m6", "text": "这条是第 6 条，若出现在 prompt 中说明仍在全量拼接。", "score": 0.60},
]


def _build_mock_conversation() -> llm_service.LLMConversationInput:
    """构造最小 conversation，用于直接调用 prompt 构建函数。"""
    return llm_service.LLMConversationInput(
        system_prompt="",
        support_mode="alzheimer",
        profile=UserProfile(
            id=MOCK_PATIENT_ID,  # type: ignore[arg-type]
            name="李奶奶",
            age=78,
            hometown="温州",
            family_info="女儿小雨",
            life_events="服装厂缝纫经历；温州老城区菜场",
            preferences="老歌",
            notes="回答要简短温和",
        ),
        recent_logs=[],
        user_message=MOCK_QUERY,
        context_text="",
        memory_summary=(
            "全量记忆-1。全量记忆-2。全量记忆-3。全量记忆-4。"
            "全量记忆-5。全量记忆-6。"
        ),
    )


def _extract_user_prompt(messages: list[dict[str, str]]) -> str:
    """取出最终发给模型的 user prompt 内容。"""
    for message in messages:
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _print_prompt_with_mock_search() -> None:
    """用 mock search_memory 验证 prompt 只拼入 top-4 语义记忆。"""
    original_search = memory_vector_service.search_memory
    calls: list[dict[str, object]] = []

    async def fake_search_memory(query: str, patient_id: str, top_k: int = 4) -> list[dict]:
        calls.append({"query": query, "patient_id": patient_id, "top_k": top_k})
        return list(MOCK_MEMORIES)

    memory_vector_service.search_memory = fake_search_memory  # type: ignore[assignment]
    try:
        conversation = _build_mock_conversation()
        resolved = llm_service._resolve_style_context(conversation)
        messages = llm_service._build_real_llm_messages(conversation, resolved)
        prompt = _extract_user_prompt(messages)
    finally:
        memory_vector_service.search_memory = original_search  # type: ignore[assignment]

    print("=== search_memory 调用参数 ===")
    print(calls[0] if calls else "未调用 search_memory")
    print()
    print("=== 最终 prompt ===")
    print(prompt)
    print()
    print("=== 验证结果 ===")
    top4_present = all(item["text"] in prompt for item in MOCK_MEMORIES[:4])
    extra_absent = all(item["text"] not in prompt for item in MOCK_MEMORIES[4:])
    fallback_absent = "全量记忆-5" not in prompt and "全量记忆-6" not in prompt
    print(f"已调用 search_memory: {'是' if calls else '否'}")
    print(f"top_k=4: {'是' if calls and calls[0].get('top_k') == 4 else '否'}")
    print(f"top-4 记忆进入 prompt: {'是' if top4_present else '否'}")
    print(f"第 5/6 条未进入 prompt: {'是' if extra_absent else '否'}")
    print(f"未使用全量 fallback 摘要: {'是' if fallback_absent else '否'}")


async def _check_real_vector_empty() -> None:
    """顺手检查真实向量库是否有数据，空库时给出操作提示。"""
    try:
        results = await memory_vector_service.search_memory(
            query=MOCK_QUERY,
            patient_id=MOCK_PATIENT_ID,
            top_k=4,
        )
    except RuntimeError as exc:
        print()
        print(f"真实向量检索不可用：{exc}")
        return
    except Exception as exc:
        print()
        print(f"真实向量检索失败：{type(exc).__name__}: {exc}")
        return

    if not results:
        print()
        print("向量库为空，请先运行 scripts/sync_memories.py")


async def main() -> int:
    _print_prompt_with_mock_search()
    await _check_real_vector_empty()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
