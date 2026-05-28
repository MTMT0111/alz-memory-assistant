"""Minimal MiniMax TTS orchestration with browser-fallback friendly responses."""

from __future__ import annotations

from dataclasses import dataclass
import binascii
import json
import os
from pathlib import Path
import re
import secrets
from time import perf_counter
from urllib import error, request

from app.config import load_local_env_file

load_local_env_file()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GENERATED_AUDIO_DIR = BASE_DIR / "static" / "generated_audio"
DEFAULT_MINIMAX_TTS_URL = "https://api.minimax.io/v1/t2a_v2"
DEFAULT_MINIMAX_TTS_MODEL = "speech-2.8-turbo"
DEFAULT_MINIMAX_TTS_VOICE_ID = "Chinese_female_young"


@dataclass(slots=True)
class TTSSpeakResult:
    success: bool
    audio_url: str
    fallback_to_browser_tts: bool
    reason: str
    provider: str
    model: str
    clean_text: str


def _clean_text(text: str) -> str:
    """Keep only short, plain text for speech output."""
    value = str(text or "").strip()
    if not value:
        return ""
    value = re.sub(r"`{1,3}.*?`{1,3}", "", value, flags=re.S)
    value = re.sub(r"[*_#>\-\[\]\(\)]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:120]


def _resolve_provider(provider: str) -> str:
    normalized = str(provider or "minimax").strip().lower()
    return normalized if normalized in {"minimax"} else "minimax"


def _save_audio_bytes(audio_bytes: bytes) -> str:
    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"tts_{secrets.token_hex(12)}.mp3"
    path = GENERATED_AUDIO_DIR / filename
    path.write_bytes(audio_bytes)
    return f"/static/generated_audio/{filename}"


def _synthesize_minimax(text: str) -> TTSSpeakResult:
    api_key = os.getenv("MINIMAX_API_KEY", "").strip()
    model = os.getenv("MINIMAX_TTS_MODEL", DEFAULT_MINIMAX_TTS_MODEL).strip() or DEFAULT_MINIMAX_TTS_MODEL
    voice_id = os.getenv("MINIMAX_TTS_VOICE_ID", DEFAULT_MINIMAX_TTS_VOICE_ID).strip() or DEFAULT_MINIMAX_TTS_VOICE_ID
    if not api_key:
        return TTSSpeakResult(
            success=False,
            audio_url="",
            fallback_to_browser_tts=True,
            reason="MINIMAX_API_KEY missing",
            provider="minimax",
            model=model,
            clean_text=text,
        )

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "language_boost": "Chinese",
        "output_format": "hex",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 0.92,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }
    req = request.Request(
        url=os.getenv("MINIMAX_TTS_URL", DEFAULT_MINIMAX_TTS_URL).strip() or DEFAULT_MINIMAX_TTS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            raw = response.read()
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:240]
        return TTSSpeakResult(
            success=False,
            audio_url="",
            fallback_to_browser_tts=True,
            reason=f"MiniMax HTTP {exc.code}: {detail or exc.reason}",
            provider="minimax",
            model=model,
            clean_text=text,
        )
    except Exception as exc:
        return TTSSpeakResult(
            success=False,
            audio_url="",
            fallback_to_browser_tts=True,
            reason=f"MiniMax request failed: {type(exc).__name__}",
            provider="minimax",
            model=model,
            clean_text=text,
        )

    try:
        data = json.loads(raw.decode("utf-8"))
        audio_hex = str(((data.get("data") or {}).get("audio")) or "").strip()
        status_code = int((((data.get("base_resp") or {}).get("status_code")) or 0))
        if status_code != 0 or not audio_hex:
            return TTSSpeakResult(
                success=False,
                audio_url="",
                fallback_to_browser_tts=True,
                reason=f"MiniMax TTS returned no audio, status_code={status_code}",
                provider="minimax",
                model=model,
                clean_text=text,
            )
        audio_bytes = binascii.unhexlify(audio_hex)
    except Exception as exc:
        return TTSSpeakResult(
            success=False,
            audio_url="",
            fallback_to_browser_tts=True,
            reason=f"MiniMax response parse failed: {type(exc).__name__}",
            provider="minimax",
            model=model,
            clean_text=text,
        )

    return TTSSpeakResult(
        success=True,
        audio_url=_save_audio_bytes(audio_bytes),
        fallback_to_browser_tts=False,
        reason="ok",
        provider="minimax",
        model=model,
        clean_text=text,
    )


def speak_text(text: str, provider: str = "minimax") -> dict[str, object]:
    """Return one JSON-friendly TTS result for the conversation page."""
    started_at = perf_counter()
    clean_text = _clean_text(text)
    if not clean_text:
        return {
            "success": False,
            "audio_url": "",
            "fallback_to_browser_tts": True,
            "reason": "empty_text",
            "provider": _resolve_provider(provider),
            "model": os.getenv("MINIMAX_TTS_MODEL", DEFAULT_MINIMAX_TTS_MODEL),
            "clean_text": "",
            "latency_ms": 0,
        }

    resolved_provider = _resolve_provider(provider)
    if resolved_provider != "minimax":
        result = TTSSpeakResult(
            success=False,
            audio_url="",
            fallback_to_browser_tts=True,
            reason=f"unsupported_provider: {provider}",
            provider=resolved_provider,
            model=os.getenv("MINIMAX_TTS_MODEL", DEFAULT_MINIMAX_TTS_MODEL),
            clean_text=clean_text,
        )
    else:
        result = _synthesize_minimax(clean_text)

    return {
        "success": result.success,
        "audio_url": result.audio_url,
        "fallback_to_browser_tts": result.fallback_to_browser_tts,
        "reason": result.reason,
        "provider": result.provider,
        "model": result.model,
        "clean_text": result.clean_text,
        "latency_ms": max(0, int(round((perf_counter() - started_at) * 1000))),
    }
