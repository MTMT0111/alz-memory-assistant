"""外部通知推送服务。

当前支持企业微信与钉钉 markdown webhook。Webhook 为空时静默跳过，
避免家庭本地部署未配置通知时影响主链路。
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import json
import os
from typing import Any
from urllib import error, request

from app.config import load_local_env_file


load_local_env_file()

NOTIFY_TIMEOUT_SECONDS = 5
_WEBHOOK_URL_OVERRIDE: str | None = None
_WEBHOOK_TYPE_OVERRIDE: str | None = None


def _env_text(name: str, default: str = "") -> str:
    """读取字符串配置，保留 shell 环境变量优先级。"""
    return str(os.getenv(name, default) or default).strip()


def _normalize_webhook_type(value: str | None) -> str:
    """限制 webhook 类型，未知值默认企业微信。"""
    clean_value = str(value or "").strip().lower()
    return clean_value if clean_value in {"wecom", "dingtalk"} else "wecom"


def get_webhook_url() -> str:
    """返回当前进程内生效的 webhook URL。"""
    if _WEBHOOK_URL_OVERRIDE is not None:
        return _WEBHOOK_URL_OVERRIDE.strip()
    return _env_text("NOTIFY_WEBHOOK_URL", "")


def get_webhook_type() -> str:
    """返回当前 webhook 类型。"""
    if _WEBHOOK_TYPE_OVERRIDE is not None:
        return _normalize_webhook_type(_WEBHOOK_TYPE_OVERRIDE)
    return _normalize_webhook_type(_env_text("NOTIFY_WEBHOOK_TYPE", "wecom"))


def get_medication_overdue_minutes() -> int:
    """读取用药超时分钟数，异常时回落到 30 分钟。"""
    try:
        return max(1, int(_env_text("NOTIFY_MEDICATION_OVERDUE_MIN", "30")))
    except ValueError:
        return 30


def get_runtime_config() -> dict[str, Any]:
    """返回设置页展示用通知配置，不暴露 webhook 明文。"""
    return {
        "configured": bool(get_webhook_url()),
        "type": get_webhook_type(),
        "overdue_minutes": get_medication_overdue_minutes(),
    }


def set_webhook(url: str, webhook_type: str) -> None:
    """仅在当前进程内更新 webhook 配置，不回写 .env。"""
    global _WEBHOOK_URL_OVERRIDE, _WEBHOOK_TYPE_OVERRIDE
    _WEBHOOK_URL_OVERRIDE = str(url or "").strip()
    _WEBHOOK_TYPE_OVERRIDE = _normalize_webhook_type(webhook_type)


def _build_payload(title: str, content: str) -> dict[str, Any]:
    """按企业微信/钉钉格式构造 markdown 消息体。"""
    clean_title = str(title or "通知").strip() or "通知"
    markdown = f"## {clean_title}\n{str(content or '').strip()}"
    if get_webhook_type() == "dingtalk":
        return {
            "msgtype": "markdown",
            "markdown": {"title": clean_title, "text": markdown},
            "at": {"isAtAll": False},
        }
    return {
        "msgtype": "markdown",
        "markdown": {"content": markdown},
    }


def _blocking_post(url: str, payload: dict[str, Any]) -> tuple[int, str]:
    """同步 POST webhook，由 asyncio.to_thread 包装。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=NOTIFY_TIMEOUT_SECONDS) as response:
        raw = response.read().decode("utf-8", errors="ignore")
        return int(response.status), raw


async def send_notify(title: str, content: str) -> bool:
    """发送外部 webhook 通知；未配置或失败均返回 False。"""
    webhook_url = get_webhook_url()
    if not webhook_url:
        return False
    try:
        status, raw = await asyncio.to_thread(_blocking_post, webhook_url, _build_payload(title, content))
        if 200 <= status < 300:
            return True
        print(f"[NOTIFY] webhook 返回异常状态: {status} {raw[:120]}")
    except (error.HTTPError, error.URLError, TimeoutError, OSError, Exception) as exc:
        print(f"[NOTIFY] webhook 发送失败: {type(exc).__name__}: {exc}")
    return False


async def notify_high_risk(patient_name: str, risk_type: str, suggestion: str) -> bool:
    """高风险事件推送给照护者。"""
    now_text = datetime.now().strftime("%H:%M")
    title = f"⚠️ 高风险提醒 — {patient_name}"
    content = (
        f"**风险类型：** {risk_type or '其他'}\n"
        f"**照护建议：** {suggestion or '请尽快查看照护看板。'}\n"
        f"**时间：** {now_text}\n"
        "请尽快查看照护看板。"
    )
    return await send_notify(title, content)


async def notify_medication_overdue(patient_name: str, medication_name: str, remind_time: str) -> bool:
    """用药超过确认窗口后推送给照护者。"""
    now_text = datetime.now().strftime("%H:%M")
    minutes = get_medication_overdue_minutes()
    title = f"💊 用药未确认 — {patient_name}"
    content = (
        f"**药品：** {medication_name}\n"
        f"**计划时间：** {remind_time}\n"
        f"**当前时间：** {now_text}\n"
        f"超过 {minutes} 分钟未确认服药。"
    )
    return await send_notify(title, content)
