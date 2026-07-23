#!/usr/bin/env python3
"""测试轻量记忆幻觉检测。"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.hallucination_guard import check_memory_leak


def main() -> int:
    """运行两个最小 case，并打印检测结果。"""
    approved_memories = [
        "妈妈年轻时在温州菜场买苹果。",
        "妈妈喜欢听老歌，下午听会更安心。",
    ]

    case1 = check_memory_leak(
        "我们可以听听老歌，也想想温州菜场买苹果的事。",
        approved_memories,
    )
    print("case1 已有记忆：", case1)

    case2 = check_memory_leak(
        "我记得你 1985年 去过张家界，还和王小明一起住过。",
        approved_memories,
    )
    print("case2 不存在记忆：", case2)

    print("case1 suspicious=false:", case1.get("suspicious") is False)
    print("case2 suspicious=true:", case2.get("suspicious") is True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
