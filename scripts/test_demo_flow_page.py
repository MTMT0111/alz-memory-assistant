#!/usr/bin/env python3
"""Smoke test /demo-flow returns 200 and contains the six guided steps."""

from __future__ import annotations

import os
from urllib.error import URLError
from urllib.request import urlopen


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
EXPECTED_STEPS = (
    "查看 Demo 患者资料",
    "查看熟悉素材库",
    "打开患者端对话",
    "查看家属端照护摘要",
    "查看聊天记录与记忆候选",
    "查看测试结果与对照评估",
)


def main() -> int:
    url = f"{BASE_URL}/demo-flow"
    print(f"GET {url}")
    try:
        with urlopen(url, timeout=15) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError, OSError) as exc:
        print(f"FAIL: cannot connect: {exc}")
        return 2
    if status != 200:
        print(f"FAIL: expected 200, got {status}")
        return 1
    missing = [step for step in EXPECTED_STEPS if step not in body]
    if missing:
        print(f"FAIL: missing demo steps: {missing}")
        return 1
    print("PASS: /demo-flow returned 200 with 6 demo steps.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
