"""Smoke test the real page chat API path for DeepSeek.

This script calls the same /chat endpoint used by /conversation. It is meant to
catch cases where provider factory tests pass but the running app still uses
mock as its default page-chat provider.
"""

from __future__ import annotations

import json
import os
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


CHAT_URL = os.getenv("CHAT_URL", "http://127.0.0.1:8000/chat")
TEST_MESSAGE = "我想听老歌"


def _post_chat() -> dict:
    payload = json.dumps({"message": TEST_MESSAGE}, ensure_ascii=False).encode("utf-8")
    request = Request(
        CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=90) as response:
        body = response.read().decode("utf-8")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise RuntimeError("chat API returned a non-object payload")
    return data


def main() -> int:
    print("Page chat DeepSeek smoke test")
    print("需要先启动服务：")
    print("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print(f"POST {CHAT_URL}")
    print(f"message: {TEST_MESSAGE}")

    try:
        data = _post_chat()
    except (URLError, TimeoutError, OSError) as exc:
        print(f"FAIL: 无法连接本地服务：{exc}")
        return 2

    diagnostics = data.get("diagnostics") or {}
    requested_provider = diagnostics.get("requested_provider") or diagnostics.get("provider") or "-"
    actual_provider = diagnostics.get("actual_provider") or diagnostics.get("provider") or "-"
    model = diagnostics.get("model") or "-"
    api_key_configured = diagnostics.get("api_key_configured")
    fallback_used = bool(diagnostics.get("fallback_used"))
    fallback_reason = diagnostics.get("fallback_reason") or "-"
    reply = data.get("reply") or diagnostics.get("final_assistant_reply") or ""

    print()
    print("Diagnostics")
    print(f"requested_provider: {requested_provider}")
    print(f"actual_provider: {actual_provider}")
    print(f"model: {model}")
    print(f"api_key_configured: {api_key_configured}")
    print(f"fallback_used: {fallback_used}")
    print(f"fallback_reason: {fallback_reason}")
    print(f"final reply: {reply}")

    bad_mock_markers = ("模拟回复", "mock reply", "lorem ipsum", "TODO")
    if any(marker in reply for marker in bad_mock_markers):
        print()
        print("FAIL: mock/fallback reply looks like a placeholder instead of a care-scene reply.")
        return 1

    if requested_provider != "deepseek":
        print()
        print(f"FAIL: 页面聊天链路没有默认请求 DeepSeek。requested_provider={requested_provider}")
        return 1

    if actual_provider == "deepseek" and model == "deepseek-v4-flash" and not fallback_used:
        print()
        print("PASS: 页面聊天链路正在使用 DeepSeek，且没有 fallback。")
        return 0

    print()
    print("FAIL: 页面聊天链路没有达到 actual_provider=deepseek 且 fallback_used=false。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
