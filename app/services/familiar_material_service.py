"""CRUD and prompt-summary helpers for familiar reminiscence materials."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Sequence

from app.database import get_connection
from app.models.familiar_material import FamiliarMaterial, MATERIAL_TYPES


TYPE_LABELS = {
    "family_photo": "家人照片",
    "voice_message": "语音留言",
    "familiar_music": "熟悉音乐",
    "old_place": "旧地点",
    "old_event": "旧事件",
    "daily_object": "日常物品",
    "sensitive_memory": "敏感记忆",
}

DEMO_MATERIALS = [
    {
        "material_type": "family_photo",
        "title": "女儿小雨照片",
        "description": "用于帮助李奶奶确认女儿小雨。",
        "related_person": "陈小雨",
        "tags": "女儿,小雨,人物识别",
    },
    {
        "material_type": "voice_message",
        "title": "小雨晚间安抚留言",
        "description": "小雨告诉妈妈晚上 8 点会联系她。",
        "related_person": "陈小雨",
        "tags": "小雨,晚上8点,安抚",
    },
    {
        "material_type": "familiar_music",
        "title": "轻柔老歌播放清单",
        "description": "用于下午焦虑时安抚。",
        "tags": "老歌,焦虑,下午",
    },
    {
        "material_type": "old_place",
        "title": "温州老城区菜场",
        "description": "李奶奶以前常去买苹果和青菜。",
        "tags": "温州,菜场,苹果,青菜",
    },
    {
        "material_type": "old_event",
        "title": "服装厂缝纫经历",
        "description": "李奶奶年轻时在服装厂做缝纫工，手很巧。",
        "tags": "服装厂,缝纫,年轻时",
    },
    {
        "material_type": "old_event",
        "title": "老伴王建国",
        "description": "已故老伴相关话题，不主动刺激性提起。",
        "related_person": "王建国",
        "tags": "老伴,老王,王建国,敏感",
        "material_type": "sensitive_memory",
        "is_sensitive": True,
        "safety_note": "患者问起时先接住情绪，不直接说去世。",
        "sensitivity_level": "high",
    },
]

TRIGGER_WORDS = {
    "family_photo": ("照片", "小雨", "女儿", "这个人", "是谁", "认不出"),
    "voice_message": ("小雨", "女儿", "回来", "联系", "电话", "留言"),
    "familiar_music": ("老歌", "歌", "音乐", "害怕", "焦虑", "不安"),
    "old_place": ("菜场", "温州", "老城区", "苹果", "青菜", "回家", "哪里"),
    "old_event": ("服装厂", "做衣服", "缝纫", "以前", "年轻"),
    "daily_object": ("药盒", "照片", "杯子", "钥匙", "苹果", "物品", "东西"),
    "sensitive_memory": ("老王", "王建国", "老伴", "想他", "回来"),
}

SCENE_TRIGGERS = {
    "family_photo": "提到家人/人物识别，可用照片关系提示。",
    "voice_message": "提到小雨/女儿/回来/焦虑，可用语音留言安抚。",
    "familiar_music": "提到老歌/音乐/焦虑，可推荐熟悉音乐。",
    "old_place": "提到旧地点/菜场/苹果/回家，可用地点记忆安抚。",
    "old_event": "提到以前/做衣服/服装厂，可用旧经历回忆引导。",
    "daily_object": "提到日常物品，可用物品线索帮助确认。",
    "sensitive_memory": "明确提到敏感人物或记忆，只使用安全提示。",
}


@dataclass(slots=True)
class MaterialMatch:
    """One material selected for the current message."""

    material: FamiliarMaterial
    reason: str
    matched_terms: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.material.id,
            "material_type": self.material.material_type,
            "type_label": TYPE_LABELS.get(self.material.material_type, self.material.material_type),
            "title": self.material.title,
            "related_person": self.material.related_person,
            "is_sensitive": self.material.is_sensitive,
            "reason": self.reason,
            "matched_terms": self.matched_terms,
        }


def _now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_int(value: Any) -> int | None:
    """把年份等输入转成整数；无法解析时保持为空。"""
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def photo_decade_from_year(year: int | None) -> str:
    """根据照片年份计算年代标签，供时间线筛选使用。"""
    if not year:
        return ""
    if year >= 2000:
        return "2000s+"
    decade = (int(year) // 10) * 10
    return f"{decade}s"


def _normalize_material_type(value: Any) -> str:
    text = _clean_text(value)
    return text if text in MATERIAL_TYPES else "old_event"


def _clean_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _clean_active(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"0", "false", "no", "off"}:
        return False
    return True


def _split_tags(text: str) -> list[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(tag).strip() for tag in parsed if str(tag).strip()]
        except Exception:
            pass
    return [tag.strip() for tag in raw.replace("，", ",").split(",") if tag.strip()]


def _normalize_tags(value: Any) -> str:
    """新版标签统一存 JSON 数组；兼容前端传逗号分隔字符串。"""
    if isinstance(value, list):
        tags = [str(item).strip() for item in value if str(item).strip()]
    else:
        tags = _split_tags(str(value or ""))
    return json.dumps(tags, ensure_ascii=False)


def _row_by_id(patient_id: int | str, material_id: int) -> FamiliarMaterial | None:
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM familiar_materials WHERE patient_id = ? AND id = ?",
            (patient_id, material_id),
        ).fetchone()
    return FamiliarMaterial.from_row(row) if row else None


def list_materials(patient_id: int | str, *, limit: int = 100) -> list[FamiliarMaterial]:
    """Return familiar materials for one patient profile."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT * FROM familiar_materials
            WHERE patient_id = ?
            ORDER BY is_sensitive ASC, is_active DESC, material_type ASC, updated_at DESC, id DESC
            LIMIT ?
            """,
            (patient_id, max(1, min(limit, 200))),
        ).fetchall()
    return [FamiliarMaterial.from_row(row) for row in rows]


def save_material(patient_id: int | str, payload: dict[str, Any], material_id: int | None = None) -> FamiliarMaterial:
    """Create or update one familiar material."""
    now = _now_text()
    normalized = {
        "material_type": _normalize_material_type(payload.get("material_type")),
        "title": _clean_text(payload.get("title")) or "未命名素材",
        "description": _clean_text(payload.get("description")),
        "related_person": _clean_text(payload.get("related_person")),
        "file_path": _clean_text(
            payload.get("file_path")
            or payload.get("url")
            or payload.get("image_url")
            or payload.get("audio_url")
            or payload.get("music_url")
        ),
        "thumbnail_url": _clean_text(payload.get("thumbnail_url") or payload.get("image_url")),
        "transcript_text": _clean_text(payload.get("transcript_text")),
        "artist": _clean_text(payload.get("artist")),
        "use_scene": _clean_text(payload.get("use_scene")),
        "suggested_use_scene": _clean_text(payload.get("suggested_use_scene")),
        "related_time": _clean_text(payload.get("related_time")),
        "sensitivity_level": _clean_text(payload.get("sensitivity_level")),
        "tags": _normalize_tags(payload.get("tags")),
        "safety_note": _clean_text(payload.get("safety_note")),
        "photo_year": _clean_int(payload.get("photo_year")),
        "story_text": _clean_text(payload.get("story_text"))[:500],
        "voice_note_path": _clean_text(payload.get("voice_note_path")),
        "is_sensitive": _clean_bool(payload.get("is_sensitive")),
        "is_active": _clean_active(payload.get("is_active")),
    }
    normalized["photo_decade"] = _clean_text(payload.get("photo_decade")) or photo_decade_from_year(normalized["photo_year"])
    if normalized["material_type"] == "sensitive_memory":
        normalized["is_sensitive"] = True

    with closing(get_connection()) as connection:
        if material_id is not None:
            existing = connection.execute(
                "SELECT id FROM familiar_materials WHERE patient_id = ? AND id = ?",
                (patient_id, material_id),
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE familiar_materials
                    SET material_type = ?,
                        title = ?,
                        description = ?,
                        related_person = ?,
                        file_path = ?,
                        thumbnail_url = ?,
                        transcript_text = ?,
                        artist = ?,
                        use_scene = ?,
                        suggested_use_scene = ?,
                        related_time = ?,
                        sensitivity_level = ?,
                        tags = ?,
                        safety_note = ?,
                        photo_year = ?,
                        photo_decade = ?,
                        story_text = ?,
                        voice_note_path = ?,
                        is_sensitive = ?,
                        is_active = ?,
                        updated_at = ?
                    WHERE patient_id = ? AND id = ?
                    """,
                    (
                        normalized["material_type"],
                        normalized["title"],
                        normalized["description"],
                        normalized["related_person"],
                        normalized["file_path"],
                        normalized["thumbnail_url"],
                        normalized["transcript_text"],
                        normalized["artist"],
                        normalized["use_scene"],
                        normalized["suggested_use_scene"],
                        normalized["related_time"],
                        normalized["sensitivity_level"],
                        normalized["tags"],
                        normalized["safety_note"],
                        normalized["photo_year"],
                        normalized["photo_decade"],
                        normalized["story_text"],
                        normalized["voice_note_path"],
                        int(normalized["is_sensitive"]),
                        int(normalized["is_active"]),
                        now,
                        patient_id,
                        material_id,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM familiar_materials WHERE patient_id = ? AND id = ?",
                    (patient_id, material_id),
                ).fetchone()
                return FamiliarMaterial.from_row(row)

        connection.execute(
            """
            INSERT INTO familiar_materials (
                patient_id, material_type, title, description, related_person,
                file_path, thumbnail_url, transcript_text, artist, use_scene,
                suggested_use_scene, related_time, sensitivity_level, tags,
                safety_note, photo_year, photo_decade, story_text, voice_note_path,
                is_sensitive, is_active, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                normalized["material_type"],
                normalized["title"],
                normalized["description"],
                normalized["related_person"],
                normalized["file_path"],
                normalized["thumbnail_url"],
                normalized["transcript_text"],
                normalized["artist"],
                normalized["use_scene"],
                normalized["suggested_use_scene"],
                normalized["related_time"],
                normalized["sensitivity_level"],
                normalized["tags"],
                normalized["safety_note"],
                normalized["photo_year"],
                normalized["photo_decade"],
                normalized["story_text"],
                normalized["voice_note_path"],
                int(normalized["is_sensitive"]),
                int(normalized["is_active"]),
                now,
                now,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM familiar_materials WHERE id = last_insert_rowid()"
        ).fetchone()
    return FamiliarMaterial.from_row(row)


def delete_material(patient_id: int | str, material_id: int) -> bool:
    """Delete one familiar material."""
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "DELETE FROM familiar_materials WHERE patient_id = ? AND id = ?",
            (patient_id, material_id),
        )
        connection.commit()
    return bool(cursor.rowcount)


def get_material_by_id(material_id: int) -> FamiliarMaterial | None:
    """按素材 id 查一条记录，用于语音说明上传等跨页面操作。"""
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM familiar_materials WHERE id = ?",
            (material_id,),
        ).fetchone()
    return FamiliarMaterial.from_row(row) if row else None


def update_voice_note_path(material_id: int, voice_note_path: str) -> FamiliarMaterial | None:
    """保存照护者录制的语音说明路径。"""
    with closing(get_connection()) as connection:
        connection.execute(
            "UPDATE familiar_materials SET voice_note_path = ?, updated_at = ? WHERE id = ?",
            (_clean_text(voice_note_path), _now_text(), material_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM familiar_materials WHERE id = ?",
            (material_id,),
        ).fetchone()
    return FamiliarMaterial.from_row(row) if row else None


def update_timeline_fields(material_id: int, payload: dict[str, Any]) -> FamiliarMaterial | None:
    """只更新相册时间线相关字段，避免覆盖旧素材信息。"""
    allowed: dict[str, Any] = {}
    if "photo_year" in payload:
        year = _clean_int(payload.get("photo_year"))
        allowed["photo_year"] = year
        allowed["photo_decade"] = _clean_text(payload.get("photo_decade")) or photo_decade_from_year(year)
    elif "photo_decade" in payload:
        allowed["photo_decade"] = _clean_text(payload.get("photo_decade"))
    if "story_text" in payload:
        allowed["story_text"] = _clean_text(payload.get("story_text"))[:500]
    if "tags" in payload:
        allowed["tags"] = _normalize_tags(payload.get("tags"))
    if not allowed:
        return get_material_by_id(material_id)

    allowed["updated_at"] = _now_text()
    assignments = ", ".join(f"{column} = ?" for column in allowed)
    values = list(allowed.values()) + [material_id]
    with closing(get_connection()) as connection:
        connection.execute(
            f"UPDATE familiar_materials SET {assignments} WHERE id = ?",
            values,
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM familiar_materials WHERE id = ?",
            (material_id,),
        ).fetchone()
    return FamiliarMaterial.from_row(row) if row else None


def timeline_materials(patient_id: int | str) -> list[FamiliarMaterial]:
    """返回时间线相册素材，优先按年份和更新时间排序。"""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT * FROM familiar_materials
            WHERE patient_id = ? AND is_active = 1
            ORDER BY COALESCE(photo_year, 9999) ASC, updated_at DESC, id DESC
            """,
            (patient_id,),
        ).fetchall()
    return [FamiliarMaterial.from_row(row) for row in rows]


def grouped_timeline(patient_id: int | str) -> dict[str, list[dict[str, Any]]]:
    """按年代分组返回相册素材，供前端瀑布流使用。"""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for material in timeline_materials(patient_id):
        key = material.photo_decade or photo_decade_from_year(material.photo_year) or "其他"
        grouped.setdefault(key, []).append(material.to_dict())
    return grouped


def seed_demo_materials(patient_id: int) -> int:
    """Create demo familiar materials once for the demo patient."""
    existing_by_title = {item.title: item for item in list_materials(patient_id)}
    created = 0
    for material in DEMO_MATERIALS:
        existing = existing_by_title.get(material["title"])
        if existing:
            if material["title"] == "老伴王建国" and existing.material_type != "sensitive_memory":
                save_material(patient_id, material, material_id=existing.id)
            continue
        save_material(patient_id, material)
        created += 1
    return created


def summarize_status(materials: Sequence[FamiliarMaterial]) -> dict[str, Any]:
    """Return a caregiver-facing configuration status summary."""
    by_type = {material_type: False for material_type in MATERIAL_TYPES}
    sensitive_count = 0
    for material in materials:
        if material.material_type in by_type:
            by_type[material.material_type] = True
        if material.is_sensitive:
            sensitive_count += 1
    return {
        "family_photo": by_type["family_photo"],
        "voice_message": by_type["voice_message"],
        "familiar_music": by_type["familiar_music"],
        "old_place": by_type["old_place"],
        "old_event": by_type["old_event"],
        "daily_object": by_type["daily_object"],
        "sensitive_memory": by_type["sensitive_memory"],
        "sensitive_count": sensitive_count,
        "total_count": len(materials),
    }


def _material_hints(material: FamiliarMaterial, *, include_type_hints: bool) -> list[str]:
    hints: list[str] = []
    if include_type_hints:
        hints.extend(TRIGGER_WORDS.get(material.material_type, ()))
    hints.extend(part.strip() for part in (material.title, material.related_person, material.artist, material.related_time) if part)
    hints.extend(_split_tags(material.tags))
    hints.extend(_split_tags(material.use_scene))
    hints.extend(_split_tags(material.suggested_use_scene))
    return list(dict.fromkeys(hint for hint in hints if hint))


def _message_match_terms(message: str, material: FamiliarMaterial) -> list[str]:
    normalized = _clean_text(message)
    if not normalized:
        return []
    hints = _material_hints(material, include_type_hints=not material.is_sensitive)
    return [hint for hint in hints if hint and hint in normalized]


def _message_triggers_material(message: str, material: FamiliarMaterial) -> bool:
    return bool(_message_match_terms(message, material))


def match_materials(patient_id: int, user_message: str, *, max_items: int = 6) -> list[MaterialMatch]:
    """Return relevant materials for one chat turn without exposing inactive items."""
    matches: list[MaterialMatch] = []
    for material in list_materials(patient_id):
        if not material.is_active:
            continue
        terms = _message_match_terms(user_message, material)
        if material.is_sensitive and not terms:
            continue
        if not material.is_sensitive and not terms:
            continue
        reason = SCENE_TRIGGERS.get(material.material_type, "当前消息命中了素材标题、人物或标签。")
        if material.is_sensitive:
            reason = "用户明确触发敏感素材，只用于安全模板和情绪承接。"
        matches.append(MaterialMatch(material=material, reason=reason, matched_terms=terms))

    if not matches and _clean_text(user_message):
        fallback = [material for material in list_materials(patient_id) if material.is_active and not material.is_sensitive][:3]
        matches = [
            MaterialMatch(material=material, reason="没有直接命中，提供少量非敏感基础线索。", matched_terms=[])
            for material in fallback
        ]

    return matches[:max_items]


def build_prompt_summary(patient_id: int, user_message: str, *, max_items: int = 6) -> str:
    """Build a compact safe material summary for the LLM prompt."""
    matches = match_materials(patient_id, user_message, max_items=max_items)
    if not matches:
        return ""

    lines: list[str] = []
    for match in matches[:max_items]:
        material = match.material
        label = TYPE_LABELS.get(material.material_type, material.material_type)
        pieces = [f"{label}：{material.title}"]
        if material.related_person:
            pieces.append(f"关联：{material.related_person}")
        if material.artist:
            pieces.append(f"艺人：{material.artist}")
        if material.use_scene or material.suggested_use_scene:
            pieces.append(f"适用场景：{material.use_scene or material.suggested_use_scene}")
        if material.description:
            pieces.append(material.description)
        if material.transcript_text:
            pieces.append(f"留言摘要：{material.transcript_text[:80]}")
        if material.is_sensitive:
            pieces.append(f"敏感素材，只在用户主动提及时参考。安全提示：{material.safety_note or '先接住情绪，不直接刺激。'}")
        pieces.append(f"匹配原因：{match.reason}")
        lines.append("；".join(pieces))

    return "\n".join(f"- {line}" for line in lines)


def get_material_or_404(patient_id: int | str, material_id: int) -> FamiliarMaterial | None:
    """Return one material if it belongs to the patient."""
    return _row_by_id(patient_id, material_id)
