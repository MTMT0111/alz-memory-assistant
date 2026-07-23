"""MiniMax TTS service with browser speechSynthesis fallback contract."""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
from time import perf_counter
from urllib import error, parse, request

from app.config import load_local_env_file

load_local_env_file()

MINIMAX_TTS_URL = "https://api.minimax.chat/v1/t2a_v2"
DEFAULT_MINIMAX_TTS_MODEL = "speech-2.8-turbo"
DEFAULT_MINIMAX_TTS_VOICE_ID = "male-qn-jingying"
TTS_TIMEOUT_SECONDS = 10


def _clean_text(text: str, max_chars: int = 500) -> str:
    """清理 Markdown 和多余空白，避免把格式符号读出来。"""
    value = str(text or "").strip()
    if not value:
        return ""
    value = re.sub(r"`{1,3}.*?`{1,3}", "", value, flags=re.S)
    value = re.sub(r"[*_#>\-\[\]\(\)]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:max_chars]


def _env_value(name: str) -> str:
    """读取环境变量，同时把示例占位值视为未配置。"""
    value = os.getenv(name, "").strip()
    if not value or value.lower().startswith("your_"):
        return ""
    return value


def _fallback(text: str, reason: str = "") -> dict[str, object]:
    """返回前端可直接降级到浏览器 speechSynthesis 的结构。"""
    payload: dict[str, object] = {
        "audio_base64": None,
        "fallback": True,
        "text": text,
    }
    if reason:
        payload["reason"] = reason
    return payload


def _decode_minimax_audio(audio_value: str) -> str:
    """MiniMax 非流式 T2A v2 通常返回 hex，这里转成前端需要的 base64 mp3。"""
    audio_text = str(audio_value or "").strip()
    if not audio_text:
        return ""

    try:
        audio_bytes = binascii.unhexlify(audio_text)
    except (binascii.Error, ValueError):
        # 若服务端配置变化返回了 base64，尽量兼容，校验成功后原样返回。
        base64.b64decode(audio_text, validate=True)
        return audio_text
    return base64.b64encode(audio_bytes).decode("ascii")


def _request_minimax_tts(text: str, voice_id: str) -> dict[str, object]:
    """同步调用 MiniMax T2A v2；外层用 asyncio.to_thread 避免阻塞事件循环。"""
    api_key = _env_value("MINIMAX_API_KEY")
    group_id = _env_value("MINIMAX_GROUP_ID")
    if not api_key:
        return _fallback(text, "MINIMAX_API_KEY missing")
    if not group_id:
        return _fallback(text, "MINIMAX_GROUP_ID missing")

    model = os.getenv("MINIMAX_TTS_MODEL", DEFAULT_MINIMAX_TTS_MODEL).strip() or DEFAULT_MINIMAX_TTS_MODEL
    query = parse.urlencode({"GroupId": group_id})
    url = f"{MINIMAX_TTS_URL}?{query}"
    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "language_boost": "Chinese",
        "output_format": "hex",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 0.9,
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
    api_request = request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(api_request, timeout=TTS_TIMEOUT_SECONDS) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        status_code = int(((data.get("base_resp") or {}).get("status_code")) or 0)
        audio_value = str(((data.get("data") or {}).get("audio")) or "")
        audio_base64 = _decode_minimax_audio(audio_value)
        if status_code != 0 or not audio_base64:
            return _fallback(text, f"MiniMax TTS returned no audio, status_code={status_code}")
        return {"audio_base64": audio_base64, "fallback": False}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:240]
        return _fallback(text, f"MiniMax HTTP {exc.code}: {detail or exc.reason}")
    except Exception as exc:
        return _fallback(text, f"MiniMax request failed: {type(exc).__name__}")


async def synthesize(text: str, voice_id: str | None = None) -> dict[str, object]:
    """合成语音；失败时不抛异常，交给前端使用浏览器朗读兜底。"""
    clean_text = _clean_text(text, max_chars=500)
    if not clean_text:
        return _fallback("", "empty_text")

    selected_voice_id = str(voice_id or DEFAULT_MINIMAX_TTS_VOICE_ID).strip() or DEFAULT_MINIMAX_TTS_VOICE_ID
    try:
        return _request_minimax_tts(clean_text, selected_voice_id)
    except Exception as exc:
        return _fallback(clean_text, f"TTS fallback: {type(exc).__name__}")


def speak_text(text: str, provider: str = "minimax") -> dict[str, object]:
    """兼容旧 /api/tts/speak 调用，内部复用新的 base64 TTS 合约。"""
    started_at = perf_counter()
    clean_text = _clean_text(text, max_chars=120)
    if str(provider or "minimax").strip().lower() != "minimax":
        result = _fallback(clean_text, f"unsupported_provider: {provider}")
    elif not clean_text:
        result = _fallback("", "empty_text")
    else:
        result = _request_minimax_tts(clean_text, os.getenv("MINIMAX_TTS_VOICE_ID", DEFAULT_MINIMAX_TTS_VOICE_ID).strip() or DEFAULT_MINIMAX_TTS_VOICE_ID)

    fallback = bool(result.get("fallback"))
    return {
        "success": not fallback,
        "audio_base64": result.get("audio_base64"),
        "audio_url": "",
        "fallback": fallback,
        "fallback_to_browser_tts": fallback,
        "text": result.get("text", clean_text),
        "reason": result.get("reason", "ok"),
        "provider": "minimax",
        "model": os.getenv("MINIMAX_TTS_MODEL", DEFAULT_MINIMAX_TTS_MODEL),
        "clean_text": clean_text,
        "latency_ms": max(0, int(round((perf_counter() - started_at) * 1000))),
    }
