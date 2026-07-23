"""本地 Ollama LLM 访问服务。

这里负责：
- 读取本地模型开关与地址配置
- 检查 Ollama 是否在线
- 发送非流式 chat 请求
- 提供运行期内存开关，供设置页动态切换
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib import error, request

from app.config import load_local_env_file


load_local_env_file()

OLLAMA_AVAILABLE_TIMEOUT_SECONDS = 3
_LOCAL_LLM_ENABLED_OVERRIDE: bool | None = None


def _env_text(name: str, default: str) -> str:
    """读取文本配置；缺失时回落到默认值。"""
    return str(os.getenv(name, default) or default).strip() or default


def _env_bool(name: str, default: bool = False) -> bool:
    """读取布尔配置，兼容常见 false/off/no 表达。"""
    value = str(os.getenv(name, "true" if default else "false") or "").strip().lower()
    return value not in {"0", "false", "off", "no"}


def is_local_enabled() -> bool:
    """返回当前是否开启本地模型优先。"""
    if _LOCAL_LLM_ENABLED_OVERRIDE is not None:
        return _LOCAL_LLM_ENABLED_OVERRIDE
    return _env_bool("LOCAL_LLM_ENABLED", default=False)


def set_local_enabled(enabled: bool) -> None:
    """仅在当前进程内切换本地优先模式，不回写 .env。"""
    global _LOCAL_LLM_ENABLED_OVERRIDE
    _LOCAL_LLM_ENABLED_OVERRIDE = bool(enabled)


def get_runtime_config() -> dict[str, Any]:
    """返回设置页需要展示的本地模型配置。"""
    timeout_text = _env_text("LOCAL_LLM_TIMEOUT", "30")
    try:
        timeout_seconds = max(1, int(timeout_text))
    except ValueError:
        timeout_seconds = 30
    return {
        "enabled": is_local_enabled(),
        "model": _env_text("LOCAL_LLM_MODEL", "qwen2.5:3b"),
        "base_url": _env_text("LOCAL_LLM_BASE_URL", "http://localhost:11434").rstrip("/"),
        "timeout": timeout_seconds,
    }


def _blocking_json_request(url: str, payload: dict[str, Any] | None, timeout: int) -> dict[str, Any]:
    """同步发出一个 JSON 请求，由 asyncio.to_thread 包装调用。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = request.Request(url=url, data=body, headers=headers, method="POST" if body is not None else "GET")
    with request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    data = json.loads(raw or "{}")
    return data if isinstance(data, dict) else {}


async def is_ollama_available() -> bool:
    """检查 Ollama 服务是否在线。"""
    config = get_runtime_config()
    url = f"{config['base_url']}/api/tags"
    try:
        await asyncio.to_thread(_blocking_json_request, url, None, OLLAMA_AVAILABLE_TIMEOUT_SECONDS)
        return True
    except (error.HTTPError, error.URLError, json.JSONDecodeError, OSError, TimeoutError, Exception):
        return False


async def chat(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 300,
) -> str:
    """调用本地 Ollama 非流式 chat 接口。"""
    config = get_runtime_config()
    url = f"{config['base_url']}/api/chat"
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": str(system_prompt or "").strip()},
            {"role": "user", "content": str(user_message or "").strip()},
        ],
        "stream": False,
        "options": {
            "num_predict": max(1, int(max_tokens or 300)),
            "temperature": 0.7,
        },
    }
    try:
        data = await asyncio.to_thread(_blocking_json_request, url, payload, int(config["timeout"]))
    except Exception as exc:  # pragma: no cover - 依赖本地运行状态
        raise RuntimeError(f"Ollama request failed: {type(exc).__name__}: {exc}") from exc

    message = data.get("message") if isinstance(data.get("message"), dict) else {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise RuntimeError("Ollama empty response")
    return content
