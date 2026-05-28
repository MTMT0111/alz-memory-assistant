#!/usr/bin/env python3
"""Smoke test /chat-history returns 200 from the running app."""

from __future__ import annotations

import os
from urllib.error import URLError
from urllib.request import urlopen


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def main() -> int:
    url = f"{BASE_URL}/chat-history"
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
    if "聊天记录" not in body:
        print("FAIL: page body does not look like chat history")
        return 1
    print("PASS: /chat-history returned 200.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
