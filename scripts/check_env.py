#!/usr/bin/env python3
"""Check real provider credentials without touching application code."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import error, parse, request


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
TIMEOUT_SECONDS = 5
TARGET_KEYS = (
    "MINIMAX_API_KEY",
    "MINIMAX_GROUP_ID",
    "OPENAI_API_KEY",
    "DEEPSEEK_API_KEY",
)


def load_env_file() -> dict[str, str]:
    """轻量读取 .env；真实 shell 环境变量优先。"""
    values: dict[str, str] = {}
    if ENV_PATH.exists():
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")

    for key in TARGET_KEYS:
        if os.getenv(key):
            values[key] = os.getenv(key, "").strip()
    return values


def is_placeholder(value: str) -> bool:
    """判断 key 是否仍是示例占位符。"""
    normalized = str(value or "").strip().lower()
    return "your_" in normalized or normalized.endswith("_here") or "_here" in normalized


def precheck_status(values: dict[str, str], key: str) -> tuple[str, str]:
    """先检查缺失和占位符，避免误请求。"""
    value = values.get(key, "").strip()
    if not value:
        return "MISSING", ""
    if is_placeholder(value):
        return "PLACEHOLDER", value
    return "", value


def http_json(method: str, url: str, *, headers: dict[str, str], payload: dict[str, object] | None = None) -> tuple[int, dict[str, object] | str]:
    """发送最小 HTTP 请求；任何异常都转成可打印结果。"""
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url=url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", errors="ignore")
            try:
                return response.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return response.status, raw[:240]
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        try:
            body: dict[str, object] | str = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = raw[:240]
        return exc.code, body
    except Exception as exc:
        return 0, f"{type(exc).__name__}: {exc}"


def detail_text(body: dict[str, object] | str) -> str:
    """压缩 provider 错误，便于一行输出。"""
    if isinstance(body, str):
        return body.strip() or "empty response"
    for key in ("error", "message", "detail"):
        value = body.get(key)
        if value:
            return json.dumps(value, ensure_ascii=False)[:240]
    base_resp = body.get("base_resp")
    if isinstance(base_resp, dict):
        message = base_resp.get("status_msg") or base_resp.get("message") or base_resp.get("status_code")
        if message:
            return str(message)[:240]
    return json.dumps(body, ensure_ascii=False)[:240]


def verify_minimax(values: dict[str, str]) -> dict[str, tuple[str, str]]:
    """MiniMax TTS 需要 API key 和 group id 同时有效。"""
    results: dict[str, tuple[str, str]] = {}
    for key in ("MINIMAX_API_KEY", "MINIMAX_GROUP_ID"):
        status, value = precheck_status(values, key)
        if status:
            results[key] = (status, value)

    if results:
        return results

    api_key = values["MINIMAX_API_KEY"].strip()
    group_id = values["MINIMAX_GROUP_ID"].strip()
    url = "https://api.minimax.chat/v1/t2a_v2?" + parse.urlencode({"GroupId": group_id})
    payload = {
        "model": "speech-2.8-turbo",
        "text": "你好",
        "stream": False,
        "output_format": "hex",
        "voice_setting": {
            "voice_id": "male-qn-jingying",
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
    status_code, body = http_json(
        "POST",
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        payload=payload,
    )
    if status_code == 200 and isinstance(body, dict) and ((body.get("data") or {}).get("audio")):
        return {
            "MINIMAX_API_KEY": ("OK", "MiniMax TTS request succeeded"),
            "MINIMAX_GROUP_ID": ("OK", "MiniMax TTS request succeeded"),
        }
    message = f"HTTP {status_code}: {detail_text(body)}" if status_code else detail_text(body)
    return {
        "MINIMAX_API_KEY": ("INVALID", message),
        "MINIMAX_GROUP_ID": ("INVALID", message),
    }


def verify_openai(values: dict[str, str]) -> tuple[str, str]:
    """OpenAI 只用 models 列表做最小鉴权检查。"""
    status, value = precheck_status(values, "OPENAI_API_KEY")
    if status:
        return status, value
    status_code, body = http_json(
        "GET",
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {value}"},
    )
    if status_code == 200:
        return "OK", "GET /v1/models succeeded"
    message = f"HTTP {status_code}: {detail_text(body)}" if status_code else detail_text(body)
    return "INVALID", message


def verify_deepseek(values: dict[str, str]) -> tuple[str, str]:
    """DeepSeek 用极短 chat completion 验证 key 可用。"""
    status, value = precheck_status(values, "DEEPSEEK_API_KEY")
    if status:
        return status, value
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "你好"}],
        "max_tokens": 8,
        "temperature": 0,
    }
    status_code, body = http_json(
        "POST",
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {value}", "Content-Type": "application/json"},
        payload=payload,
    )
    if status_code == 200:
        return "OK", "DeepSeek chat completion succeeded"
    message = f"HTTP {status_code}: {detail_text(body)}" if status_code else detail_text(body)
    return "INVALID", message


def print_result(key: str, status: str, detail: str = "") -> None:
    """统一输出格式。"""
    suffix = f": {detail}" if detail else ""
    if status == "INVALID":
        print(f"{key}: [INVALID: {detail}]")
        return
    print(f"{key}: [{status}]{suffix}")


def main() -> int:
    values = load_env_file()
    minimax_results = verify_minimax(values)
    for key in ("MINIMAX_API_KEY", "MINIMAX_GROUP_ID"):
        status, detail = minimax_results[key]
        print_result(key, status, detail)

    status, detail = verify_openai(values)
    print_result("OPENAI_API_KEY", status, detail)

    status, detail = verify_deepseek(values)
    print_result("DEEPSEEK_API_KEY", status, detail)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
