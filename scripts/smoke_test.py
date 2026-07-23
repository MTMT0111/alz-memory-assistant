#!/usr/bin/env python3
"""Report basic API smoke-test results against a running local service."""

from __future__ import annotations

import json
import wave
from io import BytesIO
from urllib import error, request


BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 5


def request_bytes(method: str, path: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    """发送请求并返回状态码和响应体；失败也只报告不抛出。"""
    req = request.Request(
        url=f"{BASE_URL}{path}",
        data=data,
        headers=headers or {},
        method=method,
    )
    try:
        with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            return response.status, response.read()
    except error.HTTPError as exc:
        return exc.code, exc.read()
    except Exception as exc:
        return 0, str(exc).encode("utf-8", errors="ignore")


def parse_json(raw: bytes) -> dict[str, object]:
    """尽量解析 JSON，解析失败返回原始摘要。"""
    try:
        parsed = json.loads(raw.decode("utf-8", errors="ignore"))
        return parsed if isinstance(parsed, dict) else {"body": parsed}
    except json.JSONDecodeError:
        return {"body": raw.decode("utf-8", errors="ignore")[:240]}


def make_silent_wav(duration_ms: int = 300, sample_rate: int = 16000) -> bytes:
    """生成一段很短的静音 wav，用于 /api/stt 上传测试。"""
    frame_count = int(sample_rate * duration_ms / 1000)
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frame_count)
    return buffer.getvalue()


def print_report(name: str, status_code: int, fields: dict[str, object]) -> None:
    """统一打印接口 smoke 结果。"""
    print(f"{name}: status={status_code} fields={json.dumps(fields, ensure_ascii=False)}")


def smoke_health() -> None:
    status_code, raw = request_bytes("GET", "/health")
    body = parse_json(raw)
    print_report("GET /health", status_code, {"body": body.get("body", body)})


def smoke_tts() -> None:
    payload = json.dumps({"text": "你好"}, ensure_ascii=False).encode("utf-8")
    status_code, raw = request_bytes(
        "POST",
        "/api/tts",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    body = parse_json(raw)
    print_report(
        "POST /api/tts",
        status_code,
        {
            "fallback": body.get("fallback"),
            "has_audio_base64": bool(body.get("audio_base64")),
            "text": body.get("text"),
            "reason": body.get("reason") or body.get("error"),
        },
    )


def smoke_stt() -> None:
    boundary = "----alz-smoke-boundary"
    wav_bytes = make_silent_wav()
    multipart = b"".join(
        [
            f"--{boundary}\r\n".encode("ascii"),
            b'Content-Disposition: form-data; name="audio"; filename="silent.wav"\r\n',
            b"Content-Type: audio/wav\r\n\r\n",
            wav_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("ascii"),
        ]
    )
    status_code, raw = request_bytes(
        "POST",
        "/api/stt",
        data=multipart,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    body = parse_json(raw)
    print_report(
        "POST /api/stt",
        status_code,
        {
            "text": body.get("text"),
            "error": body.get("error"),
            "body": body.get("body"),
        },
    )


def main() -> int:
    smoke_health()
    smoke_tts()
    smoke_stt()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
