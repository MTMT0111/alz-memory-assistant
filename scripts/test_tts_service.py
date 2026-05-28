#!/usr/bin/env python3
"""Smoke test for MiniMax TTS wrapper and browser-fallback contract."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services import tts_service


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    print("TTS service smoke test")
    raw_text = "### 李奶奶\n**我们慢慢来。** 小雨晚上会联系您。 " + ("老歌 " * 80)
    payload = tts_service.speak_text(raw_text, provider="minimax")

    _assert("clean_text" in payload, "clean_text missing from TTS payload")
    _assert(len(str(payload.get("clean_text") or "")) <= 120, "clean_text should be capped at 120 chars")
    _assert("**" not in str(payload.get("clean_text") or ""), "clean_text should remove markdown markers")
    _assert("audio_url" in payload, "audio_url missing from TTS payload")
    _assert("fallback_to_browser_tts" in payload, "fallback_to_browser_tts missing from TTS payload")

    if payload.get("success"):
        audio_url = str(payload.get("audio_url") or "")
        _assert(audio_url.startswith("/static/generated_audio/"), f"Unexpected audio_url: {audio_url}")
        file_path = PROJECT_ROOT / audio_url.lstrip("/")
        _assert(file_path.exists(), f"Generated audio file not found: {file_path}")
        print(f"PASS: MiniMax TTS returned audio at {audio_url}")
    else:
        _assert(payload.get("fallback_to_browser_tts") is True, "Fallback should be enabled on TTS failure")
        print(f"PASS: TTS fallback is ready ({payload.get('reason')})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
