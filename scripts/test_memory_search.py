#!/usr/bin/env python3
"""手动验证记忆语义检索效果。

示例：
    python3 scripts/test_memory_search.py patient_001 "妈妈年轻时喜欢什么"
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services import memory_vector_service


async def main() -> int:
    """从命令行读取 patient_id 和 query，打印 top-4 检索结果。"""
    if len(sys.argv) < 3:
        print('用法：python3 scripts/test_memory_search.py patient_001 "妈妈年轻时喜欢什么"')
        return 1

    patient_id = sys.argv[1].strip()
    query = " ".join(sys.argv[2:]).strip()
    if not patient_id or not query:
        print("patient_id 和 query 不能为空。")
        return 1

    try:
        results = await memory_vector_service.search_memory(
            query=query,
            patient_id=patient_id,
            top_k=4,
        )
    except RuntimeError as exc:
        print(f"检索失败：{exc}")
        return 1
    except Exception as exc:
        print(f"检索失败：{type(exc).__name__}: {exc}")
        return 1

    if not results:
        print("没有检索到相关记忆。")
        return 0

    for index, item in enumerate(results, start=1):
        print(f"[{index}] memory_id={item.get('memory_id', '')}")
        print(f"    score={item.get('score', '')}")
        print(f"    text={item.get('text', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
