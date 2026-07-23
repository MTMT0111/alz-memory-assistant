"""记忆候选去重与事实冲突软检测。

检测结果只作为照护者审核提示，不会阻断候选记忆保存。
"""

from __future__ import annotations

import json
import re

from app.services import llm_service, memory_vector_service


def _compact_text(value: str, limit: int = 500) -> str:
    """压缩候选文本，避免检测 prompt 过长。"""
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


async def check_duplicate(candidate_text: str, patient_id: str, threshold: float = 0.85) -> dict:
    """用向量相似度检查候选记忆是否疑似重复。"""
    clean_text = _compact_text(candidate_text)
    if not clean_text:
        return {"is_duplicate": False}

    try:
        matches = await memory_vector_service.search_memory(
            query=clean_text,
            patient_id=str(patient_id),
            top_k=1,
        )
    except Exception:
        # 向量库或依赖未就绪时，不影响候选保存。
        return {"is_duplicate": False}

    if not matches:
        return {"is_duplicate": False}

    best = matches[0]
    score = float(best.get("score") or 0)
    if score >= threshold:
        return {
            "is_duplicate": True,
            "similar_to": str(best.get("text") or ""),
            "score": round(score, 4),
        }
    return {"is_duplicate": False}


def _build_conflict_prompt(existing: str, candidate: str) -> str:
    """构造事实冲突检测 prompt。"""
    return (
        f"已有记忆：{existing}\n"
        f"候选新记忆：{candidate}\n\n"
        "请判断候选记忆和已有记忆是否存在事实冲突（如时间、人物、地点矛盾）。\n"
        "只回答 JSON：{\"conflict\": true/false, \"reason\": \"...\"}\n"
        "不要输出其他内容。"
    )


def _parse_conflict_json(content: str) -> dict:
    """解析模型返回的 JSON；解析失败交给调用方降级。"""
    text = str(content or "").strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        text = match.group(0)
    data = json.loads(text)
    return {
        "conflict": bool(data.get("conflict")),
        "reason": str(data.get("reason") or "").strip(),
    }


async def check_conflict(candidate_text: str, patient_id: str) -> dict:
    """用统一 LLM 入口检测候选记忆与最相关 top-3 已有记忆是否事实冲突。"""
    clean_text = _compact_text(candidate_text)
    if not clean_text:
        return {"conflict": False, "reason": "检测失败"}

    try:
        matches = await memory_vector_service.search_memory(
            query=clean_text,
            patient_id=str(patient_id),
            top_k=3,
        )
    except Exception:
        return {"conflict": False, "reason": "检测失败"}

    if not matches:
        return {"conflict": False, "reason": ""}

    existing = "\n".join(
        f"- {_compact_text(str(item.get('text') or ''), limit=240)}"
        for item in matches
        if str(item.get("text") or "").strip()
    )
    if not existing:
        return {"conflict": False, "reason": ""}

    try:
        content = await llm_service.chat(
            system_prompt="你只输出严格 JSON，不输出解释。",
            user_message=_build_conflict_prompt(existing, clean_text),
            max_tokens=120,
        )
        parsed = _parse_conflict_json(content)
        if parsed["conflict"] and not parsed["reason"]:
            parsed["reason"] = "候选记忆与已有记忆存在事实冲突。"
        return parsed
    except (json.JSONDecodeError, Exception):
        return {"conflict": False, "reason": "检测失败"}
