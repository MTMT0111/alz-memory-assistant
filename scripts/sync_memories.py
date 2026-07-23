#!/usr/bin/env python3
"""将 SQLite 中已审批长期记忆同步到 Chroma 向量库。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import DB_PATH
from app.services import memory_vector_service


async def main() -> int:
    """执行幂等同步；重复运行会按 memory_id 覆盖更新，不会产生重复向量。"""
    try:
        await memory_vector_service.sync_from_sqlite(str(DB_PATH))
    except RuntimeError as exc:
        print(f"同步失败：{exc}")
        return 1

    count = memory_vector_service.get_last_sync_count()
    print(f"已同步 {count} 条已审批记忆到向量库。")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
