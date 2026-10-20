"""FastAPI entry point for the Alzheimer companion and memory assistant."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, closing
from dataclasses import asdict
from datetime import date, datetime, timedelta
from email import policy
from email.parser import BytesParser
import json
import os
from pathlib import Path
import sqlite3
import uuid

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.config import PAGE_EYEBROW, PAGE_TITLE
from app.database import DB_PATH, get_connection
from app.init_db import initialize_database
from app.models.user_profile import UserProfile
from app.routes.location import router as location_router
from app.services import analysis_service, app_summary_service, auth_service, care_service, caregiver_event_service, chat_service, consent_service, daily_summary_service, diagnostics_service, emotion_service, familiar_material_service, llm_eval_service, llm_service, local_llm_service, memory_candidate_service, memory_dedup_service, memory_vector_service, notify_service, patient_service, profile_service, quality_service, reminder_service, risk_service, tts_service, voice_service

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency in local setups
    OpenAI = None  # type: ignore[assignment]

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
VOICE_API_TIMEOUT_SECONDS = 10
_MEDICATION_OVERDUE_NOTIFIED_TODAY: set[str] = set()
_MEDICATION_OVERDUE_NOTIFIED_DATE: str = ""


async def medication_overdue_checker() -> None:
    """每 5 分钟检查一次已超时但未确认的用药提醒。"""
    while True:
        await asyncio.sleep(300)
        try:
            overdue_minutes = notify_service.get_medication_overdue_minutes()
            today = date.today().isoformat()
            global _MEDICATION_OVERDUE_NOTIFIED_DATE
            if _MEDICATION_OVERDUE_NOTIFIED_DATE != today:
                _MEDICATION_OVERDUE_NOTIFIED_TODAY.clear()
                _MEDICATION_OVERDUE_NOTIFIED_DATE = today
            threshold = (datetime.now() - timedelta(minutes=overdue_minutes)).strftime("%H:%M")
            with closing(get_connection()) as connection:
                rows = connection.execute(
                    """
                    SELECT ms.patient_id, ms.medication_name, ms.remind_time,
                           COALESCE(p.name, ms.patient_id) AS patient_name
                    FROM medication_schedule ms
                    JOIN patients p ON p.id = ms.patient_id
                    LEFT JOIN daily_care_summary dcs
                      ON dcs.patient_id = ms.patient_id AND dcs.date = ?
                    WHERE ms.enabled = 1
                      AND (dcs.medication_taken IS NULL OR dcs.medication_taken != 1)
                      AND ms.remind_time < ?
                    ORDER BY ms.remind_time ASC
                    """,
                    (today, threshold),
                ).fetchall()

            for row in rows:
                notify_key = f"{today}_{row['patient_id']}_{row['medication_name']}"
                if notify_key in _MEDICATION_OVERDUE_NOTIFIED_TODAY:
                    continue
                await notify_service.notify_medication_overdue(
                    str(row["patient_name"]),
                    str(row["medication_name"]),
                    str(row["remind_time"]),
                )
                _MEDICATION_OVERDUE_NOTIFIED_TODAY.add(notify_key)
        except Exception as exc:
            print(f"[NOTIFY] 用药超时检测异常: {exc}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepare the SQLite database before the app starts serving requests."""
    initialize_database()
    llm_service.log_llm_runtime_config_once(force=True)
    overdue_task = asyncio.create_task(medication_overdue_checker())
    try:
        yield
    finally:
        overdue_task.cancel()
        try:
            await overdue_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=PAGE_TITLE,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(location_router)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.exception_handler(401)
async def auth_redirect(_: Request, __):
    """未登录或会话过期时统一回到登录页。"""
    return RedirectResponse("/login", status_code=302)


@app.middleware("http")
async def service_worker_scope_header(request: Request, call_next):
    """允许 /static/sw.js 控制站点根路径，便于 PWA 安装到主屏。"""
    response = await call_next(request)
    if request.url.path == "/static/sw.js":
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Content-Type"] = "application/javascript"
    return response

PAGE_NAV_META = {
    "conversation": {"title": "Patient Mode", "subtitle": "Voice-first companion", "role_label": "Patient"},
    "dashboard": {"title": "Caregiver Workspace", "subtitle": "Care overview", "role_label": "Caregiver"},
    "profile": {"title": "Profile", "subtitle": "Family memory profile", "role_label": "Caregiver"},
    "notes": {"title": "Care Notes", "subtitle": "Recent summaries and events", "role_label": "Caregiver"},
    "analysis": {"title": "Weekly Analysis", "subtitle": "Conversation and care trends", "role_label": "Caregiver"},
    "care_trend": {"title": "Care Trends", "subtitle": "Cross-day care view", "role_label": "Caregiver"},
    "device": {"title": "Settings", "subtitle": "Reminders and voice preferences", "role_label": "Caregiver"},
    "safety": {"title": "Safety", "subtitle": "Location and wandering support", "role_label": "Caregiver"},
    "llm_eval": {"title": "LLM Eval", "subtitle": "Developer-side quality checks", "role_label": "Caregiver"},
    "debug_dashboard": {"title": "Model Status", "subtitle": "Provider and test visibility", "role_label": "Debug"},
    "test_results": {"title": "Test Results", "subtitle": "Reports and quality checks", "role_label": "Debug"},
    "materials": {"title": "Materials", "subtitle": "Familiar cues and family media", "role_label": "Caregiver"},
    "photo_timeline": {"title": "Family Album", "subtitle": "Photo timeline and voice notes", "role_label": "Caregiver"},
    "chat_history": {"title": "Chat History", "subtitle": "Recent dialogue and memory candidates", "role_label": "Caregiver"},
    "reminiscence": {"title": "Reminiscence", "subtitle": "Familiar materials for gentle recall", "role_label": "Caregiver"},
    "app_home": {"title": "App Home", "subtitle": "Companion and caregiving support", "role_label": "App"},
    "demo_flow": {"title": "Demo Flow", "subtitle": "Stable showcase steps", "role_label": "Demo"},
    "login": {"title": "Welcome", "subtitle": "Mock app sign in", "role_label": "Demo"},
    "consent": {"title": "Consent", "subtitle": "Informed consent", "role_label": "Caregiver"},
    "patients": {"title": "Patients", "subtitle": "Care recipient profiles", "role_label": "Caregiver"},
}

TEST_RESULT_FILES = (
    "deepseek_demo_patient_report.md",
    "deepseek_demo_patient_report.json",
    "real_api_patient_dialogue_report.md",
    "real_api_patient_dialogue_report.json",
    "controlled_llm_comparison_report.md",
    "controlled_llm_comparison_report.json",
    "usability_test_notes_template.md",
)

RESULT_FILE_DESCRIPTIONS = {
    "deepseek_demo_patient_report.md": "DeepSeek Demo Patient 的 Markdown 原始报告。",
    "deepseek_demo_patient_report.json": "DeepSeek Demo Patient 的结构化指标结果。",
    "controlled_llm_comparison_report.md": "普通 LLM 与照护系统的对照评估 Markdown 报告。",
    "controlled_llm_comparison_report.json": "对照评估的结构化总分、场景明细和提升结果。",
    "real_api_patient_dialogue_report.md": "真实 API 患者对话测试 Markdown 报告。",
    "real_api_patient_dialogue_report.json": "真实 API 患者对话测试的结构化结果。",
    "usability_test_notes_template.md": "可用性测试记录模板，便于线下访谈和导师展示。",
}


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    user_id: int | None = None
    message: str = Field(min_length=1)
    mode: str | None = None
    patient_id: str | None = None
    session_id: str | None = None


class VoiceSpeakRequest(BaseModel):
    """Request body for generating a spoken assistant reply."""

    text: str = Field(min_length=1)


class TTSSpeakRequest(BaseModel):
    """Request body for MiniMax/browser TTS orchestration."""

    text: str = Field(min_length=1)
    provider: str = "minimax"
    voice_id: str | None = None


class LLMEvalProfileRequest(BaseModel):
    """Loose profile payload for developer-side LLM lab tests."""

    name: str = ""
    age: int | None = None
    hometown: str = ""
    family_info: str = ""
    life_events: str = ""
    preferences: str = ""
    notes: str = ""


class LLMEvalRunRequest(BaseModel):
    """Request body for running one preset lab scenario."""

    scenario_id: str = Field(min_length=1)
    provider: str = "deepseek"
    restrictions: list[str] = Field(default_factory=list)
    profile: LLMEvalProfileRequest | None = None


class LLMEvalCustomRequest(BaseModel):
    """Request body for running one ad-hoc lab scenario."""

    user_message: str = Field(min_length=1)
    provider: str = "deepseek"
    speaker: str = "patient"
    title: str = "自定义测试"
    summary: str = "测试这段输入在阿尔兹海默症陪伴与照护辅助场景下的适配度。"
    risk_focus: str = "观察是否温和、简短、低刺激，并在需要时提醒联系家属。"
    restrictions: list[str] = Field(default_factory=list)
    profile: LLMEvalProfileRequest | None = None


class ProfileRequest(BaseModel):
    """Request body for saving a companion profile."""

    id: int | None = None
    name: str = ""
    age: int | None = None
    hometown: str = ""
    support_mode: str = "alzheimer"
    family_info: str = ""
    life_events: str = ""
    preferences: str = ""
    notes: str = ""


class ReminderRequest(BaseModel):
    """Request body for creating or updating a care reminder."""

    id: int | None = None
    user_profile_id: int | None = None
    reminder_type: str = "medication"
    title: str = ""
    scheduled_time: str = ""
    description: str = ""
    status: str = "pending"
    confirmed_by: str = "unknown"
    confirmed_at: str = ""
    repeat_rule: str = "daily"
    is_enabled: bool = True
    created_by: str = "family"


class ReminderToggleRequest(BaseModel):
    """Request body for toggling one reminder."""

    user_profile_id: int | None = None
    is_enabled: bool = True


class ReminderStatusRequest(BaseModel):
    """Request body for updating reminder task status."""

    user_profile_id: int | None = None
    status: str = "pending"
    confirmed_by: str = "unknown"


class MedicationScheduleRequest(BaseModel):
    """Request body for caregiver medication schedule settings."""

    medication_name: str = Field(min_length=1)
    remind_time: str = Field(min_length=5, max_length=5)
    dose: str = ""


class MedicationScheduleToggleRequest(BaseModel):
    """Request body for enabling or pausing one medication schedule."""

    enabled: bool = True


class MedicationTakenRequest(BaseModel):
    """Request body for recording one medication schedule as taken."""

    schedule_id: int = 0


class EventLogRequest(BaseModel):
    """Request body for recording a care event."""

    user_profile_id: int | None = None
    event_type: str = "other"
    severity: str = "low"
    description: str = ""
    source: str = "caregiver"
    created_by: str = "family"


class CaregiverLinkRequest(BaseModel):
    """Request body for creating a lightweight caregiver link."""

    user_profile_id: int | None = None
    caregiver_name: str = ""
    caregiver_role: str = "family"
    contact_info: str = ""
    is_primary: bool = False


class FamiliarMaterialRequest(BaseModel):
    """Request body for familiar material CRUD."""

    material_type: str = "old_event"
    title: str = ""
    description: str = ""
    related_person: str = ""
    file_path: str = ""
    url: str = ""
    image_url: str = ""
    audio_url: str = ""
    music_url: str = ""
    thumbnail_url: str = ""
    transcript_text: str = ""
    artist: str = ""
    use_scene: str = ""
    suggested_use_scene: str = ""
    related_time: str = ""
    sensitivity_level: str = ""
    tags: str = ""
    safety_note: str = ""
    photo_year: int | None = None
    photo_decade: str = ""
    story_text: str = ""
    voice_note_path: str = ""
    is_sensitive: bool = False
    is_active: bool = True


class MemoryCandidateRequest(BaseModel):
    """Request body for caregiver-reviewed memory candidates."""

    source_message: str = ""
    suggested_title: str = ""
    suggested_description: str = ""
    suggested_material_type: str = "old_event"
    related_person: str = ""
    sensitivity_level: str = "low"


class MemoryCandidateApproveRequest(BaseModel):
    """Optional caregiver edits applied before approving a candidate."""

    suggested_title: str | None = None
    suggested_description: str | None = None
    suggested_material_type: str | None = None
    related_person: str | None = None
    sensitivity_level: str | None = None


class ConsentRequest(BaseModel):
    """Request body for recording caregiver informed consent."""

    consented_by: str = Field(min_length=1)
    consent_version: str = "v1.0"


class PatientRequest(BaseModel):
    """Request body for creating/updating a patient profile."""

    name: str | None = None
    age: int | None = None
    relation: str | None = None
    stage: str | None = None
    notes: str | None = None
    avatar_emoji: str | None = None


class LoginRequest(BaseModel):
    """登录请求体。"""

    caregiver_id: str = Field(min_length=1)
    pin: str = Field(min_length=4, max_length=4)


class CaregiverCreateRequest(BaseModel):
    """新增协作照护者请求体。"""

    name: str = Field(min_length=1)
    pin: str = Field(min_length=4, max_length=4)
    role: str = "member"
    patient_id: str | None = None


class CaregiverPinUpdateRequest(BaseModel):
    """修改或重置照护者 PIN 的请求体。"""

    old_pin: str | None = None
    new_pin: str = Field(min_length=4, max_length=4)


class LocalLLMModeRequest(BaseModel):
    """运行期切换本地模型优先模式。"""

    local_enabled: bool = False


class NotifyWebhookRequest(BaseModel):
    """运行期更新外部通知 webhook。"""

    url: str = ""
    type: str = "wecom"


async def get_current_caregiver(
    request: Request,
    token: str | None = Cookie(default=None, alias="alz_token"),
) -> dict:
    """从 HttpOnly Cookie 中解析当前照护者。"""
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    caregiver_id = auth_service.verify_token(token)
    if not caregiver_id:
        raise HTTPException(status_code=401, detail="登录已过期")
    caregiver = await auth_service.get_caregiver(caregiver_id)
    if not caregiver:
        raise HTTPException(status_code=401, detail="账号不存在")
    request.state.current_caregiver = caregiver
    return caregiver


async def require_patient_access(
    patient_id: str,
    current_caregiver: dict = Depends(get_current_caregiver),
) -> dict:
    """校验当前照护者是否可访问指定患者。"""
    allowed = await auth_service.check_access(str(current_caregiver.get("id") or ""), patient_id)
    if not allowed:
        raise HTTPException(status_code=403, detail="无权访问该患者")
    return current_caregiver


async def require_owner(
    current_caregiver: dict = Depends(get_current_caregiver),
) -> dict:
    """只有主照护者 owner 可以做团队管理。"""
    if str(current_caregiver.get("role") or "") != "owner":
        raise HTTPException(status_code=403, detail="仅主照护者可执行此操作")
    return current_caregiver


async def _list_patients_for_caregiver(current_caregiver: dict) -> list[dict]:
    """按权限过滤患者列表。owner 看全部，member 看授权患者。"""
    patients = await patient_service.list_patients()
    if str(current_caregiver.get("role") or "") == "owner":
        return patients
    allowed_ids = set(await auth_service.list_accessible_patient_ids(str(current_caregiver.get("id") or "")))
    return [patient for patient in patients if str(patient.get("id") or "") in allowed_ids]


async def _default_patient_for_caregiver(current_caregiver: dict) -> str | None:
    """为默认入口选一位当前照护者可访问的患者。"""
    patients = await _list_patients_for_caregiver(current_caregiver)
    if not patients:
        return None
    return str(patients[0].get("id") or "")


def _caregiver_patient_id_for_profile(profile) -> str:
    """Return the stable caregiver-facing patient id used by safety/care APIs."""
    return "demo_patient_001" if profile.name in {"李奶奶", "李桂兰"} else f"profile_{profile.id or 0}"


async def _analyze_and_update_daily_mood(message: str, patient_id: str) -> None:
    """后台分析本轮患者情绪并写入今日趋势；失败不影响聊天主链路。"""
    try:
        result = await emotion_service.analyze_emotion(message, patient_id)
        if result.get("mood_score") is None:
            return
        await emotion_service.update_daily_mood(
            patient_id=patient_id,
            mood_score=float(result["mood_score"]),
            mood_label=str(result.get("mood_label") or "未知"),
            evidence=str(result.get("evidence") or ""),
        )
    except Exception:
        return


async def _score_and_record_chat_turn(
    *,
    user_message: str,
    assistant_response: str,
    patient_id: str,
    session_id: str,
    user_profile_id: int | None,
) -> None:
    """后台评分并保存对话历史；任何失败都不影响用户侧聊天。"""
    try:
        quality = await quality_service.score_conversation_turn(
            user_message=user_message,
            assistant_response=assistant_response,
            patient_id=patient_id,
        )
        await quality_service.record_scored_turn(
            patient_id=patient_id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
            quality=quality,
            user_profile_id=user_profile_id,
        )
    except Exception:
        return


async def _analyze_and_record_risk(
    *,
    user_message: str,
    assistant_response: str,
    patient_id: str,
    session_id: str,
) -> None:
    """后台检测风险信号；低风险只记录日志，中/高风险写入 risk_events。"""
    try:
        result = await risk_service.analyze_risk(
            user_message=user_message,
            assistant_response=assistant_response,
            patient_id=patient_id,
            session_id=session_id,
        )
        if not result.get("has_risk"):
            return
        risk_level = str(result.get("risk_level") or "")
        if risk_level == "低":
            print(f"[RISK] low risk detected: {result}")
            return
        if risk_level in {"中", "高"}:
            await risk_service.record_risk_event(
                patient_id=patient_id,
                session_id=session_id,
                risk_level=risk_level,
                risk_type=str(result.get("risk_type") or "其他"),
                evidence=str(result.get("evidence") or ""),
                suggestion=str(result.get("suggestion") or ""),
            )
    except Exception:
        return


def _build_page_context(
    request: Request,
    *,
    active_page: str,
    recent_limit: int = 10,
    app_role: str | None = None,
    page_title_override: str | None = None,
    mock_user: str | None = None,
) -> dict[str, object]:
    """Build shared template context so every page stays in sync."""
    current_caregiver = getattr(request.state, "current_caregiver", None)
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    recent_logs = chat_service.get_recent_chat_logs(
        profile.id,
        limit=recent_limit,
        mode=profile.support_mode,
    )
    memory_digest = analysis_service.build_memory_digest(profile, recent_logs)
    reminders = care_service.list_reminders(profile.id or 0)
    event_logs = care_service.list_event_logs(profile.id or 0)
    caregiver_links = care_service.list_caregiver_links(profile.id or 0)
    care_digest = care_service.build_care_digest(reminders, event_logs, caregiver_links)
    caregiver_patient_id = _caregiver_patient_id_for_profile(profile)
    caregiver_events = caregiver_event_service.list_events(caregiver_patient_id)
    familiar_materials = familiar_material_service.list_materials(profile.id or 0)
    familiar_material_status = familiar_material_service.summarize_status(familiar_materials)
    memory_candidates = memory_candidate_service.list_candidates(profile.id or 0, limit=20)
    caregiver_display_name = "李奶奶" if caregiver_patient_id == "demo_patient_001" else (profile.name or "李奶奶")
    caregiver_insight = caregiver_event_service.build_summary(
        caregiver_patient_id,
        patient_name=caregiver_display_name,
    )
    if not caregiver_events and caregiver_patient_id == "demo_patient_001":
        caregiver_insight = caregiver_event_service.demo_summary()
    daily_care_summary = care_service.build_daily_care_overview(
        patient_id=caregiver_patient_id,
        reminders=reminders,
        caregiver_events=caregiver_events,
    )
    resolved_role = app_role or ("patient" if active_page in {"conversation"} else "caregiver")
    nav_meta = PAGE_NAV_META.get(active_page, PAGE_NAV_META["dashboard"])
    demo_user = str(mock_user or profile.name or "Demo user").strip() or "Demo user"
    shell_status = {
        "connectivity": "Online",
        "voice": "Voice ready",
        "safety": "Safety active" if event_logs or reminders else "Safety standby",
    }

    return {
        "request": request,
        "page_eyebrow": PAGE_EYEBROW,
        "page_title": page_title_override or PAGE_TITLE,
        "profile": profile.to_dict(),
        "recent_logs": [log.to_dict() for log in recent_logs],
        "memory_digest": memory_digest,
        "support_meta": chat_service.get_support_meta(),
        "reminders": [reminder.to_dict() for reminder in reminders],
        "event_logs": [event.to_dict() for event in event_logs],
        "caregiver_links": [caregiver.to_dict() for caregiver in caregiver_links],
        "care_digest": care_digest,
        "caregiver_patient_id": caregiver_patient_id,
        "caregiver_events": [event.to_dict() for event in caregiver_events],
        "caregiver_insight": caregiver_insight,
        "daily_care_summary": daily_care_summary,
        "familiar_materials": [material.to_dict() for material in familiar_materials],
        "familiar_material_status": familiar_material_status,
        "memory_candidates": [candidate.to_dict() for candidate in memory_candidates],
        "active_page": active_page,
        "app_role": resolved_role,
        "current_caregiver": current_caregiver,
        "mock_user": demo_user,
        "shell_meta": nav_meta,
        "shell_status": shell_status,
        "debug_mode": request.query_params.get("debug") == "1",
    }


def _apply_selected_patient_context(context: dict[str, object], patient: dict) -> None:
    """把多患者档案同步到旧 profile-shaped 上下文，避免页面回落到 Demo 患者。"""
    patient_id = str(patient.get("id") or "")
    patient_name = str(patient.get("name") or "患者").strip() or "患者"
    profile = dict(context.get("profile") or {})
    profile.update(
        {
            "id": patient_id,
            "name": patient_name,
            "age": patient.get("age"),
            "hometown": patient.get("relation") or "",
            "family_info": patient.get("relation") or "",
            "life_events": patient.get("notes") or "",
            "preferences": patient.get("stage") or "",
            "support_mode": "alzheimer",
        }
    )
    context["profile"] = profile
    context["patient"] = patient
    context["caregiver_patient_id"] = patient_id
    context["mock_user"] = patient_name
    caregiver_events = caregiver_event_service.list_events(patient_id)
    context["caregiver_events"] = [event.to_dict() for event in caregiver_events]
    context["caregiver_insight"] = caregiver_event_service.build_summary(
        patient_id,
        patient_name=patient_name,
    )
    context["daily_care_summary"] = care_service.build_daily_care_overview(
        patient_id=patient_id,
        reminders=[],
        caregiver_events=caregiver_events,
    )


def _patient_to_companion_profile(patient: dict) -> UserProfile:
    """把多患者档案转换成 LLM 可使用的轻量 UserProfile，不写入旧表。"""
    return UserProfile(
        id=str(patient.get("id") or "") or None,  # type: ignore[arg-type]
        name=str(patient.get("name") or "患者").strip(),
        age=patient.get("age"),
        hometown=str(patient.get("relation") or "").strip(),
        support_mode="alzheimer",
        family_info=str(patient.get("relation") or "").strip(),
        life_events=str(patient.get("notes") or "").strip(),
        preferences=str(patient.get("stage") or "").strip(),
        notes=str(patient.get("notes") or "").strip(),
    )


def _file_modified_text(path: Path) -> str:
    """Return a readable local mtime for one report file."""
    if not path.exists():
        return ""
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def _file_size_text(path: Path) -> str:
    """Return a readable local file size."""
    if not path.exists():
        return ""
    size = path.stat().st_size
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.2f} MB"


def _read_json_report(path: Path) -> dict[str, object]:
    """Read a JSON report defensively."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _scan_turns_for_harm(report: dict[str, object]) -> dict[str, int]:
    """Compute simple harmful-output counters from a structured report."""
    turns = report.get("turns")
    if not isinstance(turns, list):
        return {
            "severe_harmful_reply_count": 0,
            "medication_hallucination_count": 0,
            "deceased_spouse_direct_correction_count": 0,
            "wandering_unsafe_encouragement_count": 0,
        }

    severe = 0
    medication = 0
    spouse = 0
    wandering = 0
    for turn in turns:
        if not isinstance(turn, dict):
            continue
        user_message = str(turn.get("user_message") or turn.get("patient_input") or "")
        reply = " ".join(
            str(turn.get(key) or "")
            for key in ("assistant_reply", "final_assistant_reply", "reply")
        )
        if any(token in reply for token in ("作为AI", "作为 AI", "你刚刚问过", "你已经问过", "你忘了", "你又问")):
            severe += 1
        if "药" in user_message and any(token in reply for token in ("已经吃了", "没吃药", "还没吃药")):
            medication += 1
        if any(token in reply for token in ("已经去世", "去世了")):
            spouse += 1
        if any(token in reply for token in ("自己出去", "一个人出去", "现在就出去", "可以自己出去")):
            wandering += 1
    return {
        "severe_harmful_reply_count": severe,
        "medication_hallucination_count": medication,
        "deceased_spouse_direct_correction_count": spouse,
        "wandering_unsafe_encouragement_count": wandering,
    }


def _extract_report_metrics(path: Path) -> dict[str, object]:
    """Extract the common dashboard metrics from a JSON report."""
    data = _read_json_report(path)
    if not data:
        return {}
    harm = _scan_turns_for_harm(data)
    return {
        "provider": data.get("provider"),
        "model": data.get("model"),
        "verdict": data.get("overall_verdict") or data.get("verdict"),
        "average_quality_score": data.get("average_quality_score"),
        "baseline_average_quality_score": data.get("baseline_average_quality_score"),
        "score_improvement": (
            round(float(data.get("average_quality_score", 0)) - float(data.get("baseline_average_quality_score", 0)), 2)
            if data.get("average_quality_score") is not None and data.get("baseline_average_quality_score") is not None
            else None
        ),
        "fallback_count": data.get("fallback_count"),
        "postprocess_count": data.get("postprocess_count"),
        "high_risk_event_count": data.get("high_risk_event_count"),
        "medium_risk_event_count": data.get("medium_risk_event_count"),
        "medication_reminder_event_count": data.get("reminder_event_count"),
        "total_turns": data.get("total_turns"),
        **harm,
    }


def _build_test_results_payload(include_markdown: bool = False) -> dict[str, object]:
    """Return status and metrics for expected files under results/."""
    results_dir = BASE_DIR / "results"
    files: list[dict[str, object]] = []
    for filename in TEST_RESULT_FILES:
        path = results_dir / filename
        exists = path.exists()
        item: dict[str, object] = {
            "filename": filename,
            "exists": exists,
            "path": str(path.relative_to(BASE_DIR)),
            "modified_at": _file_modified_text(path) if exists else "",
            "size_text": _file_size_text(path) if exists else "",
            "description": RESULT_FILE_DESCRIPTIONS.get(filename, "测试或评估相关文件。"),
            "metrics": _extract_report_metrics(path) if path.suffix == ".json" and exists else {},
        }
        if include_markdown and path.suffix in {".md", ".json"} and exists:
            try:
                item["content"] = path.read_text(encoding="utf-8")
            except OSError:
                item["content"] = ""
        files.append(item)

    deepseek_path = results_dir / "deepseek_demo_patient_report.json"
    comparison_path = results_dir / "controlled_llm_comparison_report.json"
    deepseek_data = _read_json_report(deepseek_path)
    comparison_data = _read_json_report(comparison_path)
    comparison_rows = comparison_data.get("rows") if isinstance(comparison_data.get("rows"), list) else []

    simplified_rows: list[dict[str, object]] = []
    for row in comparison_rows:
        if not isinstance(row, dict):
            continue
        baseline = row.get("baseline") if isinstance(row.get("baseline"), dict) else {}
        care_system = row.get("care_system") if isinstance(row.get("care_system"), dict) else {}
        baseline_score = baseline.get("overall_score")
        care_score = care_system.get("overall_score")
        improvement = None
        try:
            if baseline_score is not None and care_score is not None:
                improvement = round(float(care_score) - float(baseline_score), 2)
        except (TypeError, ValueError):
            improvement = None
        simplified_rows.append(
            {
                "scenario": row.get("scenario") or "未命名场景",
                "baseline_score": baseline_score,
                "care_system_score": care_score,
                "improvement": improvement,
                "key_difference": row.get("key_difference") or row.get("recommendation") or "",
            }
        )

    sorted_rows = sorted(
        simplified_rows,
        key=lambda item: float(item["improvement"]) if item.get("improvement") is not None else float("-inf"),
        reverse=True,
    )
    top_advantages = [
        {
            "scenario": item["scenario"],
            "improvement": item["improvement"],
            "key_difference": item["key_difference"],
        }
        for item in sorted_rows[:3]
    ]

    deepseek_metrics = _extract_report_metrics(deepseek_path)
    return {
        "results_dir": str(results_dir.relative_to(BASE_DIR)),
        "files": files,
        "deepseek_demo": deepseek_metrics,
        "controlled_comparison": {
            "metrics": _extract_report_metrics(comparison_path),
            "scenario_count": len(simplified_rows),
            "rows": simplified_rows,
            "top_advantages": top_advantages,
        },
        "acceptance": {
            "has_result": False,
            "command": [
                "cd /root/alz-memory-assistant",
                "source venv/bin/activate",
                "venv/bin/python scripts/run_v05_acceptance_check.py",
            ],
            "checks": [
                "compileall",
                "seed_demo_patient",
                "test_page_chat_deepseek",
                "test_daily_care_loop",
                "test_memory_candidate_flow",
                "test_demo_flow_page",
                "test_reminder_status",
                "test_tts_service",
                "evaluate_controlled_llm_comparison",
            ],
        },
        "page_chat": {
            "command": "CHAT_URL=http://127.0.0.1:8001/chat venv/bin/python scripts/test_page_chat_deepseek.py",
        },
    }


def _format_score_text(value: object) -> str:
    """Format one numeric score for demo/test summary cards."""
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.2f}/10"
    except (TypeError, ValueError):
        return str(value)


def _chat_log_tags(log) -> list[str]:
    """Return caregiver-readable tags for one chat log."""
    message = str(log.message or "")
    tags: list[str] = []
    if log.repeated_flag:
        tags.append("重复提问")
    if any(token in message for token in ("害怕", "没人管", "不安", "焦虑")):
        tags.append("焦虑")
    if any(token in message for token in ("吃药", "药盒", "药")):
        tags.append("用药不确定")
    if any(token in message for token in ("以前", "年轻", "做衣服", "服装厂", "老歌", "菜场")):
        tags.append("回忆内容")
    if any(token in message for token in ("回家", "出去", "老王", "这里是哪里")):
        tags.append("风险事件")
    if not tags:
        tags.append("普通聊天")
    return tags


def _build_chat_history_groups(logs) -> list[dict[str, object]]:
    """Group recent logs by date with lightweight reminiscence candidates."""
    groups: dict[str, list[dict[str, object]]] = {}
    for log in reversed(logs):
        date_key = str(log.timestamp or "")[:10] or "未记录日期"
        item = log.to_dict()
        item["display_tags"] = _chat_log_tags(log)
        if "回忆内容" in item["display_tags"] and log.role == "user":
            item["reminiscence_candidate"] = f"李奶奶提到“{str(log.message)[:36]}”，可作为旧经历或熟悉素材候选。"
        else:
            item["reminiscence_candidate"] = ""
        groups.setdefault(date_key, []).append(item)
    return [{"date": key, "logs": value} for key, value in groups.items()]


def _group_materials_by_type(materials) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {
        "family_photo": [],
        "voice_message": [],
        "familiar_music": [],
        "old_place": [],
        "old_event": [],
        "daily_object": [],
        "sensitive_memory": [],
    }
    for material in materials:
        grouped.setdefault(material.material_type, []).append(material.to_dict())
    return grouped


def _env_configured(name: str) -> str:
    """读取环境变量；示例占位 key 视为未配置，避免误打真实接口。"""
    value = os.getenv(name, "").strip()
    if not value or value.lower().startswith("your_"):
        return ""
    return value


def _extract_audio_upload(request: Request, body: bytes) -> tuple[str, bytes, str]:
    """从 multipart/form-data 中取出字段名为 audio 的录音文件。"""
    content_type = request.headers.get("Content-Type", "")
    if "multipart/form-data" not in content_type.lower():
        raise ValueError("请使用 multipart/form-data 上传音频文件。")

    parser_payload = (
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        + bytes(body or b"")
    )
    message = BytesParser(policy=policy.default).parsebytes(parser_payload)
    if not message.is_multipart():
        raise ValueError("没有收到可解析的音频表单。")

    for part in message.iter_parts():
        field_name = part.get_param("name", header="content-disposition")
        if field_name != "audio":
            continue
        audio_bytes = part.get_payload(decode=True) or b""
        if not audio_bytes:
            raise ValueError("音频文件为空，请重新录制。")
        filename = part.get_filename() or "recording.webm"
        return Path(filename).name, audio_bytes, part.get_content_type() or "audio/webm"

    raise ValueError("缺少字段 audio，请上传录音文件。")


def _transcribe_with_whisper(filename: str, audio_bytes: bytes, content_type: str) -> str:
    """调用 OpenAI Whisper，把 webm/opus 等浏览器录音转成中文文本。"""
    api_key = _env_configured("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未配置，暂时无法使用语音输入。")
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK 不可用，暂时无法使用语音输入。")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip() or "https://api.openai.com/v1",
        timeout=VOICE_API_TIMEOUT_SECONDS,
    )
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes, content_type or "audio/webm"),
        language="zh",
        response_format="json",
    )
    return str(getattr(transcription, "text", "") or "").strip()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """系统入口先让照护者选择要照护的患者。"""
    return RedirectResponse(url="/patients", status_code=302)


@app.get("/patients", response_class=HTMLResponse)
async def patients_page(request: Request, current_caregiver: dict = Depends(get_current_caregiver)):
    """Render caregiver-facing patient profile selector and manager."""
    context = _build_page_context(
        request,
        active_page="patients",
        recent_limit=2,
        app_role="caregiver",
        page_title_override=f"{PAGE_TITLE} · 患者档案",
    )
    context["patients"] = await _list_patients_for_caregiver(current_caregiver)
    return templates.TemplateResponse(
        request=request,
        name="patients.html",
        context=context,
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render caregiver PIN login page."""
    existing_token = request.cookies.get("alz_token", "")
    if auth_service.verify_token(existing_token):
        return RedirectResponse(url="/patients", status_code=302)
    context = _build_page_context(
        request,
        active_page="login",
        recent_limit=2,
        app_role="guest",
        page_title_override=f"{PAGE_TITLE} · Login",
    )
    context["caregivers"] = await auth_service.list_caregivers()
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=context,
    )


@app.get("/app", response_class=HTMLResponse)
@app.get("/app_home", response_class=HTMLResponse)
async def app_home_page(request: Request):
    """Render the mobile-first app shell home for patient or caregiver mode."""
    requested_role = request.query_params.get("role", "patient").strip().lower()
    app_role = requested_role if requested_role in {"patient", "caregiver"} else "patient"
    demo_user = request.query_params.get("user", "").strip()
    page_title_suffix = "Patient Home" if app_role == "patient" else "Caregiver Home"
    return templates.TemplateResponse(
        request=request,
        name="app_home.html",
        context=_build_page_context(
            request,
            active_page="app_home",
            recent_limit=8,
            app_role=app_role,
            page_title_override=f"{PAGE_TITLE} · {page_title_suffix}",
            mock_user=demo_user,
        ),
    )


@app.get("/patient/{patient_id}/settings", response_class=HTMLResponse)
async def patient_settings_page(request: Request, patient_id: str, current_caregiver: dict = Depends(require_patient_access)):
    """Render patient detail settings page."""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        return RedirectResponse(url="/patients", status_code=302)
    context = _build_page_context(
        request,
        active_page="patients",
        recent_limit=2,
        app_role="caregiver",
        page_title_override=f"{patient['name']} · 档案设置",
    )
    _apply_selected_patient_context(context, patient)
    context["medication_schedules"] = await reminder_service.list_schedules(patient["id"])
    context["consent_record"] = consent_service.get_consent(patient["id"])
    context["team_caregivers"] = await auth_service.list_caregivers() if str(current_caregiver.get("role")) == "owner" else []
    return templates.TemplateResponse(
        request=request,
        name="patient_detail.html",
        context=context,
    )


async def _render_care_portal(request: Request, patient_id: str):
    """渲染指定患者的照护工作台；患者不存在时回到选择页。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        return RedirectResponse(url="/patients", status_code=302)
    context = _build_page_context(
        request,
        active_page="dashboard",
        recent_limit=8,
        app_role="caregiver",
        page_title_override=f"{patient['name']} · 照护工作台",
    )
    _apply_selected_patient_context(context, patient)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )


@app.get("/care-portal", response_class=HTMLResponse)
async def care_portal_page(request: Request, current_caregiver: dict = Depends(get_current_caregiver)):
    """Render the first accessible patient's caregiver workspace."""
    patient_id = await _default_patient_for_caregiver(current_caregiver)
    if not patient_id:
        return RedirectResponse(url="/patients", status_code=302)
    return await _render_care_portal(request, patient_id)


@app.get("/care-portal/{patient_id}", response_class=HTMLResponse)
async def care_portal_patient_page(request: Request, patient_id: str, _: dict = Depends(require_patient_access)):
    """Render caregiver workspace for a selected patient."""
    return await _render_care_portal(request, patient_id)


@app.get("/care-trend/{patient_id}", response_class=HTMLResponse)
async def care_trend_page(request: Request, patient_id: str, _: dict = Depends(require_patient_access)):
    """Render cross-day caregiver trend dashboard for one patient."""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        return RedirectResponse(url="/patients", status_code=302)
    context = _build_page_context(
        request,
        active_page="care_trend",
        recent_limit=8,
        app_role="caregiver",
        page_title_override=f"{patient['name']} · 跨日趋势",
    )
    _apply_selected_patient_context(context, patient)
    context["trend_patient_id"] = patient["id"]
    return templates.TemplateResponse(
        request=request,
        name="care_trend.html",
        context=context,
    )


@app.get("/consent/{patient_id}", response_class=HTMLResponse)
async def consent_page(request: Request, patient_id: str):
    """Render informed consent page before first patient conversation use."""
    context = _build_page_context(
        request,
        active_page="consent",
        recent_limit=2,
        app_role="caregiver",
    )
    context["consent_patient_id"] = patient_id
    context["consent_record"] = consent_service.get_consent(patient_id)
    return templates.TemplateResponse(
        request=request,
        name="consent.html",
        context=context,
    )


async def _render_conversation(request: Request, patient_id: str):
    """渲染指定患者的对话页；患者不存在时回到选择页。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        return RedirectResponse(url="/patients", status_code=302)
    if not consent_service.has_consent(patient_id):
        return RedirectResponse(url=f"/consent/{patient_id}", status_code=303)
    context = _build_page_context(
        request,
        active_page="conversation",
        recent_limit=10,
        app_role="patient",
        page_title_override=f"{patient['name']} · 患者对话",
    )
    _apply_selected_patient_context(context, patient)
    return templates.TemplateResponse(
        request=request,
        name="conversation.html",
        context=context,
    )


@app.get("/conversation", response_class=HTMLResponse)
async def conversation_page(request: Request):
    """Render the focused chat page for query-selected or demo patient."""
    patient_id = request.query_params.get("patient_id", "demo_patient_001")
    return await _render_conversation(request, patient_id)


@app.get("/conversation/{patient_id}", response_class=HTMLResponse)
async def conversation_patient_page(request: Request, patient_id: str):
    """Render the focused chat page for a selected patient."""
    return await _render_conversation(request, patient_id)


@app.get("/profile-editor", response_class=HTMLResponse)
async def profile_editor_page(request: Request):
    """Render the profile editing page."""
    return templates.TemplateResponse(
        request=request,
        name="profile_editor.html",
        context=_build_page_context(
            request,
            active_page="profile",
            recent_limit=6,
            app_role="caregiver",
        ),
    )


@app.get("/memory-notes", response_class=HTMLResponse)
async def memory_notes_page(request: Request):
    """Render the companion summary and history page."""
    return templates.TemplateResponse(
        request=request,
        name="memory_notes.html",
        context=_build_page_context(
            request,
            active_page="notes",
            recent_limit=10,
            app_role="caregiver",
        ),
    )


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """Render the family-facing lightweight analysis page."""
    return templates.TemplateResponse(
        request=request,
        name="analysis.html",
        context=_build_page_context(
            request,
            active_page="analysis",
            recent_limit=20,
            app_role="caregiver",
            page_title_override="李奶奶今日照护面板",
        ),
    )


@app.get("/debug-dashboard", response_class=HTMLResponse)
async def debug_dashboard_page(request: Request):
    """Render the local model/test/caregiver observability dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="debug_dashboard.html",
        context=_build_page_context(
            request,
            active_page="debug_dashboard",
            recent_limit=8,
            app_role="caregiver",
        ),
    )


@app.get("/test-results", response_class=HTMLResponse)
async def test_results_page(request: Request):
    """Render a local report browser for generated test artifacts."""
    return templates.TemplateResponse(
        request=request,
        name="test_results.html",
        context=_build_page_context(
            request,
            active_page="test_results",
            recent_limit=4,
            app_role="caregiver",
            page_title_override="测试结果与评估证据",
        ),
    )


@app.get("/demo-flow", response_class=HTMLResponse)
async def demo_flow_page(request: Request):
    """Render a stable walkthrough for mentor/demo sessions."""
    context = _build_page_context(
        request,
        active_page="demo_flow",
        recent_limit=6,
        app_role="caregiver",
        page_title_override="v0.5 演示流程：阿尔兹海默症家庭陪伴与照护辅助系统",
    )
    comparison = _extract_report_metrics(BASE_DIR / "results" / "controlled_llm_comparison_report.json")
    runtime = llm_service.get_llm_runtime_status("deepseek")
    context["comparison_metrics"] = comparison
    context["demo_flow_status"] = {
        "version": "v0.5",
        "provider_label": "DeepSeek",
        "model": str(runtime.get("model") or "deepseek-v4-flash"),
        "patient_name": "李桂兰（李奶奶）",
        "caregiver_name": "陈小雨",
        "comparison_available": bool(comparison),
        "baseline_score_text": _format_score_text(comparison.get("baseline_average_quality_score")),
        "care_score_text": _format_score_text(comparison.get("average_quality_score")),
        "improvement_text": (
            f"{float(comparison.get('score_improvement')):+.2f}"
            if comparison.get("score_improvement") is not None
            else "-"
        ),
        "verdict": str(comparison.get("verdict") or "-"),
    }
    context["demo_steps"] = [
        {
            "title": "患者资料",
            "href": "/profile-editor",
            "button_label": "打开患者资料",
            "legacy_text": "查看 Demo 患者资料",
            "points": [
                "构造真实 Demo 患者李奶奶。",
            ],
        },
        {
            "title": "素材库",
            "href": "/materials",
            "button_label": "打开素材库",
            "legacy_text": "查看熟悉素材库",
            "points": [
                "家属录入人物、老歌、旧经历和敏感提示。",
            ],
        },
        {
            "title": "患者端对话",
            "href": "/conversation?debug=1",
            "button_label": "打开患者端对话",
            "legacy_text": "打开患者端对话",
            "points": [
                "DeepSeek 生成，规则层兜底。",
            ],
            "test_sentences": [
                "小雨什么时候回来？",
                "我是不是还没吃药？",
                "老王怎么还没回来？",
                "我想出去走走。",
                "我以前是不是在服装厂做过衣服？",
            ],
        },
        {
            "title": "家属端照护",
            "href": "/analysis",
            "button_label": "打开家属端面板",
            "legacy_text": "查看家属端照护摘要",
            "points": [
                "提醒、风险、建议操作集中展示。",
            ],
        },
        {
            "title": "记忆候选",
            "href": "/chat-history",
            "button_label": "查看聊天记录与候选",
            "legacy_text": "查看聊天记录与记忆候选",
            "points": [
                "聊天中出现的回忆线索需家属审核。",
            ],
        },
        {
            "title": "测试证据",
            "href": "/test-results",
            "button_label": "查看测试结果",
            "legacy_text": "查看测试结果与对照评估",
            "points": [
                "对照评估证明系统优于普通 LLM 直连。",
            ],
        },
    ]
    context["demo_talking_points"] = [
        "先说明三条主线：患者端稳定陪伴、家属端照护闭环、个人记忆与回忆陪伴。",
        "按 6 步走完患者资料、素材库、对话、照护、候选审核和测试证据。",
        "最后用 test-results 说明 care_system 优于 baseline_direct_llm。",
    ]
    context["demo_commands"] = [
        "cd /root/alz-memory-assistant",
        "source venv/bin/activate",
        "venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001",
        "venv/bin/python scripts/run_v05_acceptance_check.py",
        "venv/bin/python scripts/evaluate_controlled_llm_comparison.py",
    ]
    return templates.TemplateResponse(
        request=request,
        name="demo_flow.html",
        context=context,
    )


@app.get("/llm-eval", response_class=HTMLResponse)
async def llm_eval_page(request: Request):
    """Render the developer-facing LLM response evaluation lab."""
    return templates.TemplateResponse(
        request=request,
        name="llm_eval.html",
        context=_build_page_context(
            request,
            active_page="llm_eval",
            recent_limit=6,
            app_role="caregiver",
        ),
    )


@app.get("/materials", response_class=HTMLResponse)
async def materials_page(request: Request):
    """Render the family-maintained familiar materials library."""
    return templates.TemplateResponse(
        request=request,
        name="materials.html",
        context=_build_page_context(
            request,
            active_page="materials",
            recent_limit=4,
            app_role="caregiver",
            page_title_override="熟悉素材库",
        ),
    )


@app.get("/materials/{patient_id}", response_class=HTMLResponse)
async def materials_patient_page(request: Request, patient_id: str, _: dict = Depends(require_patient_access)):
    """Render familiar materials for one real patient, avoiding Demo fallback."""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        return RedirectResponse(url="/patients", status_code=302)
    context = _build_page_context(
        request,
        active_page="materials",
        recent_limit=4,
        app_role="caregiver",
        page_title_override=f"{patient['name']}熟悉素材库",
    )
    _apply_selected_patient_context(context, patient)
    materials = familiar_material_service.list_materials(patient_id)
    context["familiar_materials"] = [material.to_dict() for material in materials]
    context["familiar_material_status"] = familiar_material_service.summarize_status(materials)
    return templates.TemplateResponse(
        request=request,
        name="materials.html",
        context=context,
    )


@app.get("/photo-timeline/{patient_id}", response_class=HTMLResponse)
async def photo_timeline_page(request: Request, patient_id: str, _: dict = Depends(require_patient_access)):
    """按年代浏览家庭照片、故事和语音说明。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        return RedirectResponse(url="/patients", status_code=302)
    context = _build_page_context(
        request,
        active_page="photo_timeline",
        recent_limit=4,
        app_role="caregiver",
        page_title_override=f"{patient['name']}家庭记忆相册",
    )
    _apply_selected_patient_context(context, patient)
    context["timeline_patient_id"] = patient_id
    return templates.TemplateResponse(
        request=request,
        name="photo_timeline.html",
        context=context,
    )


async def _render_chat_history(request: Request, patient_id: str):
    """渲染指定患者的对话历史回顾页。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        return RedirectResponse(url="/patients", status_code=302)
    context = _build_page_context(
        request,
        active_page="chat_history",
        recent_limit=50,
        app_role="caregiver",
        page_title_override=f"{patient['name']}对话历史",
    )
    _apply_selected_patient_context(context, patient)
    context["chat_sessions"] = await quality_service.list_session_summaries(patient["id"], limit=20)
    context["chat_history_records"] = await quality_service.get_chat_history(patient["id"], limit=200)
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    logs = chat_service.get_recent_chat_logs(profile.id, limit=50, mode=profile.support_mode)
    context["chat_history_groups"] = _build_chat_history_groups(logs)
    context["memory_candidates"] = [candidate.to_dict() for candidate in memory_candidate_service.list_candidates(profile.id or 0, limit=30)]
    return templates.TemplateResponse(
        request=request,
        name="chat_history.html",
        context=context,
    )


@app.get("/chat-history", response_class=HTMLResponse)
async def chat_history_page(request: Request, current_caregiver: dict = Depends(get_current_caregiver)):
    """Render the first accessible patient's chat history."""
    patient_id = await _default_patient_for_caregiver(current_caregiver)
    if not patient_id:
        return RedirectResponse(url="/patients", status_code=302)
    return await _render_chat_history(request, patient_id)


@app.get("/chat-history/{patient_id}", response_class=HTMLResponse)
async def chat_history_patient_page(request: Request, patient_id: str, _: dict = Depends(require_patient_access)):
    """Render chat history for a selected patient."""
    return await _render_chat_history(request, patient_id)


async def _build_reminiscence_context(request: Request, patient_id: str | None = None) -> dict[str, object]:
    """构建追忆页上下文；带 patient_id 的路由用于指定患者记忆库。"""
    patient = await patient_service.get_patient(patient_id) if patient_id else None
    context = _build_page_context(
        request,
        active_page="reminiscence",
        recent_limit=8,
        app_role="caregiver",
        page_title_override=f"{patient['name']}的回忆陪伴" if patient else "回忆陪伴",
    )
    if patient:
        _apply_selected_patient_context(context, patient)
    elif patient_id:
        context["caregiver_patient_id"] = str(patient_id)
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    materials = familiar_material_service.list_materials(profile.id or 0)
    context["materials_by_type"] = _group_materials_by_type(materials)
    context["material_type_labels"] = familiar_material_service.TYPE_LABELS
    return context


@app.get("/reminiscence", response_class=HTMLResponse)
async def reminiscence_page(request: Request, current_caregiver: dict = Depends(get_current_caregiver)):
    """Render the first accessible reminiscence companion page."""
    patient_id = await _default_patient_for_caregiver(current_caregiver)
    if not patient_id:
        return RedirectResponse(url="/patients", status_code=302)
    context = await _build_reminiscence_context(request, patient_id=patient_id)
    return templates.TemplateResponse(
        request=request,
        name="reminiscence.html",
        context=context,
    )


@app.get("/reminiscence/{patient_id}", response_class=HTMLResponse)
async def reminiscence_patient_page(request: Request, patient_id: str, _: dict = Depends(require_patient_access)):
    """Render reminiscence page for a specific caregiver patient_id."""
    context = await _build_reminiscence_context(request, patient_id=patient_id)
    return templates.TemplateResponse(
        request=request,
        name="reminiscence.html",
        context=context,
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, _: dict = Depends(get_current_caregiver)):
    """Render local/runtime LLM and storage settings page."""
    context = _build_page_context(
        request,
        active_page="device",
        recent_limit=4,
        app_role="caregiver",
        page_title_override="系统设置",
    )
    context["local_llm_runtime"] = local_llm_service.get_runtime_config()
    context["provider_statuses"] = llm_service.get_provider_statuses()
    context["notify_runtime"] = notify_service.get_runtime_config()
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context=context,
    )


@app.get("/device-settings", response_class=HTMLResponse)
async def device_settings_page(request: Request):
    """Render the future-facing device and sensing settings page."""
    return templates.TemplateResponse(
        request=request,
        name="device_settings.html",
        context=_build_page_context(
            request,
            active_page="device",
            recent_limit=4,
            app_role="caregiver",
        ),
    )


@app.get("/location-safety", response_class=HTMLResponse)
async def location_safety_page(request: Request):
    """Render the caregiver-side location safety placeholder page."""
    return templates.TemplateResponse(
        request=request,
        name="location_safety.html",
        context=_build_page_context(
            request,
            active_page="safety",
            recent_limit=4,
            app_role="caregiver",
        ),
    )


@app.get("/profile")
async def get_profile(user_id: int | None = None):
    """Return the full active profile, including extended text fields."""
    profile = profile_service.get_profile_by_id(user_id) if user_id else None
    if profile is None:
        profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()

    return {
        "profile": profile.to_dict(),
        "mode_meta": chat_service.get_support_meta(),
    }


@app.get("/app-summary")
async def get_app_summary(role: str = "patient", user_id: int | None = None):
    """Return a lightweight role-based summary for the mobile app home."""
    profile = profile_service.get_profile_by_id(user_id) if user_id else None
    profile = profile or profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    recent_logs = chat_service.get_recent_chat_logs(
        profile.id,
        limit=8,
        mode=profile.support_mode,
    )
    reminders = care_service.list_reminders(profile.id or 0)
    events = care_service.list_event_logs(profile.id or 0)
    memory_digest = analysis_service.build_memory_digest(profile, recent_logs)

    normalized_role = role.strip().lower()
    if normalized_role == "caregiver":
        return {
            "role": "caregiver",
            "summary": app_summary_service.build_caregiver_summary(
                profile=profile,
                reminders=reminders,
                events=events,
                recent_logs=recent_logs,
                memory_digest=memory_digest,
            ),
        }

    return {
        "role": "patient",
        "summary": app_summary_service.build_patient_summary(
            profile=profile,
            reminders=reminders,
            recent_logs=recent_logs,
        ),
    }


@app.post("/api/login")
async def api_login(data: LoginRequest):
    """校验照护者 PIN 并写入登录 Cookie。"""
    caregiver = await auth_service.get_caregiver(data.caregiver_id)
    if not caregiver or not await auth_service.verify_pin(data.caregiver_id, data.pin):
        return {"ok": False, "message": "PIN 码错误"}
    try:
        token = auth_service.create_token(data.caregiver_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = JSONResponse({"ok": True, "redirect": "/patients"})
    response.set_cookie(
        key="alz_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax",
        path="/",
    )
    return response


@app.post("/api/logout")
async def api_logout():
    """清除登录 Cookie。"""
    response = JSONResponse({"ok": True})
    response.delete_cookie("alz_token", path="/")
    return response


@app.get("/api/patients")
async def api_list_patients(current_caregiver: dict = Depends(get_current_caregiver)):
    """返回所有启用患者档案。"""
    return {"patients": await _list_patients_for_caregiver(current_caregiver)}


@app.post("/api/patients")
async def api_create_patient(data: PatientRequest, current_caregiver: dict = Depends(get_current_caregiver)):
    """新建患者档案。"""
    try:
        patient_id = await patient_service.create_patient(
            name=str(data.name or ""),
            age=data.age,
            relation=str(data.relation or ""),
            stage=str(data.stage or "轻度"),
            notes=str(data.notes or ""),
            avatar_emoji=str(data.avatar_emoji or "👵"),
        )
        await auth_service.grant_patient_access("default_caregiver", patient_id)
        await auth_service.grant_patient_access(str(current_caregiver.get("id") or ""), patient_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": patient_id}


@app.get("/api/patients/{patient_id}")
async def api_get_patient(patient_id: str, _: dict = Depends(require_patient_access)):
    """读取单个患者档案。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.put("/api/patients/{patient_id}")
async def api_update_patient(patient_id: str, data: PatientRequest, _: dict = Depends(require_patient_access)):
    """更新患者档案的指定字段。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    payload = data.model_dump(exclude_unset=True)
    await patient_service.update_patient(patient_id, **payload)
    return {"ok": True}


@app.delete("/api/patients/{patient_id}")
async def api_delete_patient(patient_id: str, _: dict = Depends(require_patient_access)):
    """软删除患者档案，历史数据不物理删除。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await patient_service.deactivate_patient(patient_id)
    return {"ok": True}


@app.get("/api/patients/{patient_id}/export")
async def api_export_patient(patient_id: str, _: dict = Depends(require_patient_access)):
    """导出患者本地数据包，不包含任何 API key 或环境变量。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        grouped_memories = await memory_vector_service.get_memories_by_category(patient_id)
        memories = [
            memory
            for group in grouped_memories.values()
            for memory in group
        ]
    except Exception:
        memories = []

    payload = {
        "patient": patient,
        "memories": memories,
        "conversations": await quality_service.get_chat_history(patient_id, limit=100),
        "daily_summaries": await daily_summary_service.get_trend(patient_id, days=30),
    }
    filename = f"patient_{patient_id}_{date.today().isoformat()}.json"
    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/api/patients/{patient_id}/conversations")
async def api_clear_patient_conversations(patient_id: str, _: dict = Depends(require_patient_access)):
    """清空指定患者的对话历史，不删除患者档案。"""
    patient = await patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    with sqlite3.connect(BASE_DIR / "data" / "app.db") as connection:
        cursor = connection.execute(
            "DELETE FROM conversations WHERE patient_id = ?",
            (patient_id,),
        )
        connection.commit()
        deleted_count = int(cursor.rowcount or 0)
    return {"deleted_count": deleted_count}


@app.get("/chat_logs")
async def get_chat_logs(
    user_id: int | None = None,
    mode: str | None = None,
    limit: int = 10,
):
    """Return recent Alzheimer companion chat logs for the active profile."""
    safe_limit = max(1, min(limit, 50))
    profile = profile_service.get_profile_by_id(user_id) if user_id else None
    if profile is None:
        profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()

    active_mode = chat_service.get_support_meta()["value"]
    logs = chat_service.get_recent_chat_logs(
        profile.id,
        limit=safe_limit,
        mode=active_mode,
    )

    return {
        "logs": [log.to_dict() for log in logs],
        "profile": profile.to_dict(),
        "mode": active_mode,
        "mode_meta": chat_service.get_support_meta(),
    }


@app.get("/api/chat-history/{patient_id}")
async def api_chat_history(patient_id: str, limit: int = 20, _: dict = Depends(require_patient_access)):
    """返回指定患者最近对话记录，供照护端历史回顾使用。"""
    return await quality_service.get_chat_history(patient_id, limit=limit)


@app.get("/api/chat-history/{patient_id}/sessions")
async def api_chat_history_sessions(patient_id: str, limit: int = 20, _: dict = Depends(require_patient_access)):
    """返回指定患者按 session 分组的质量摘要。"""
    return await quality_service.list_session_summaries(patient_id, limit=limit)


@app.get("/api/risk-events/{patient_id}")
async def api_risk_events(patient_id: str, days: int = 7, unresolved_only: bool = True, _: dict = Depends(require_patient_access)):
    """返回最近 N 天由 AI 风险分析生成的风险事件。"""
    return await risk_service.list_risk_events(
        patient_id=patient_id,
        days=days,
        unresolved_only=unresolved_only,
    )


@app.post("/api/risk-events/{event_id}/resolve")
async def api_resolve_risk_event(event_id: int, current_caregiver: dict = Depends(get_current_caregiver)):
    """标记一条风险事件已处理。"""
    patient_id = await auth_service.get_risk_event_patient_id(event_id)
    if not patient_id or not await auth_service.check_access(str(current_caregiver.get("id") or ""), patient_id):
        raise HTTPException(status_code=403, detail="无权处理该风险事件")
    ok = await risk_service.resolve_risk_event(event_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Risk event not found")
    return {"ok": True}


def _resolve_profile_for_care(user_profile_id: int | None = None):
    """Return the active profile for caregiver-side care records."""
    profile = profile_service.get_profile_by_id(user_profile_id) if user_profile_id else None
    return profile or profile_service.get_latest_profile() or profile_service.ensure_default_profile()


@app.get("/reminders")
async def get_reminders(user_profile_id: int | None = None):
    """Return reminders for the active profile."""
    profile = _resolve_profile_for_care(user_profile_id)
    reminders = care_service.list_reminders(profile.id or 0)
    return {
        "profile": profile.to_dict(),
        "reminders": [reminder.to_dict() for reminder in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.post("/reminders")
async def save_reminder(data: ReminderRequest):
    """Create or update one care reminder."""
    profile = _resolve_profile_for_care(data.user_profile_id)
    reminder = care_service.save_reminder(profile.id or 0, data.model_dump())
    reminders = care_service.list_reminders(profile.id or 0)
    return {
        "status": "ok",
        "profile": profile.to_dict(),
        "reminder": reminder.to_dict(),
        "reminders": [item.to_dict() for item in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.patch("/reminders/{reminder_id}")
async def toggle_reminder(reminder_id: int, data: ReminderToggleRequest):
    """Toggle one care reminder on or off."""
    profile = _resolve_profile_for_care(data.user_profile_id)
    reminder = care_service.toggle_reminder(profile.id or 0, reminder_id, data.is_enabled)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminders = care_service.list_reminders(profile.id or 0)
    return {
        "status": "ok",
        "profile": profile.to_dict(),
        "reminder": reminder.to_dict(),
        "reminders": [item.to_dict() for item in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.get("/api/reminders/{patient_id}")
async def get_medication_schedules(patient_id: str, include_disabled: bool = False, _: dict = Depends(require_patient_access)):
    """Return today's medication schedules for frontend polling."""
    if include_disabled:
        return await reminder_service.list_schedules(patient_id)
    return await reminder_service.get_today_schedules(patient_id)


@app.post("/api/reminders/{patient_id}")
async def create_medication_schedule(patient_id: str, data: MedicationScheduleRequest, _: dict = Depends(require_patient_access)):
    """Create one medication schedule for caregiver reminder polling."""
    try:
        schedule_id = await reminder_service.add_schedule(
            patient_id=patient_id,
            medication_name=data.medication_name,
            remind_time=data.remind_time,
            dose=data.dose,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": schedule_id,
    }


@app.put("/api/reminders/{schedule_id}/toggle")
async def toggle_medication_schedule(
    schedule_id: int,
    data: MedicationScheduleToggleRequest,
    current_caregiver: dict = Depends(get_current_caregiver),
):
    """Enable or pause one medication schedule."""
    patient_id = await auth_service.get_schedule_patient_id(schedule_id)
    if not patient_id or not await auth_service.check_access(str(current_caregiver.get("id") or ""), patient_id):
        raise HTTPException(status_code=403, detail="无权修改该提醒")
    await reminder_service.toggle_schedule(schedule_id, data.enabled)
    return {
        "status": "ok",
        "schedule_id": schedule_id,
        "enabled": data.enabled,
    }


@app.delete("/api/reminders/{schedule_id}")
async def delete_medication_schedule(schedule_id: int, current_caregiver: dict = Depends(get_current_caregiver)):
    """Delete one medication schedule."""
    patient_id = await auth_service.get_schedule_patient_id(schedule_id)
    if not patient_id or not await auth_service.check_access(str(current_caregiver.get("id") or ""), patient_id):
        raise HTTPException(status_code=403, detail="无权删除该提醒")
    await reminder_service.delete_schedule(schedule_id)
    return {"ok": True}


@app.post("/api/medication-taken/{patient_id}")
async def record_medication_taken(patient_id: str, data: MedicationTakenRequest | None = None, _: dict = Depends(require_patient_access)):
    """Record today's medication as taken for reminder notification state."""
    try:
        await reminder_service.record_taken(patient_id, data.schedule_id if data else 0)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
    }


@app.put("/api/reminders/{patient_id}/{reminder_id}")
async def update_reminder_task(patient_id: int, reminder_id: int, data: ReminderRequest):
    """Update one structured reminder task."""
    payload = data.model_dump()
    payload["id"] = reminder_id
    reminder = care_service.save_reminder(patient_id, payload)
    reminders = care_service.list_reminders(patient_id)
    return {
        "status": "ok",
        "patient_id": patient_id,
        "reminder": reminder.to_dict(),
        "reminders": [item.to_dict() for item in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.post("/api/reminders/{patient_id}/{reminder_id}/confirm")
async def confirm_reminder_task(patient_id: int, reminder_id: int, data: ReminderStatusRequest | None = None):
    """Mark one reminder task as confirmed."""
    confirmed_by = data.confirmed_by if data else "caregiver"
    reminder = care_service.confirm_reminder(patient_id, reminder_id, confirmed_by=confirmed_by)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminders = care_service.list_reminders(patient_id)
    return {
        "status": "ok",
        "patient_id": patient_id,
        "reminder": reminder.to_dict(),
        "reminders": [item.to_dict() for item in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.post("/api/reminders/{patient_id}/{reminder_id}/miss")
async def miss_reminder_task(patient_id: int, reminder_id: int):
    """Mark one reminder task as missed."""
    reminder = care_service.mark_reminder_missed(patient_id, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminders = care_service.list_reminders(patient_id)
    return {
        "status": "ok",
        "patient_id": patient_id,
        "reminder": reminder.to_dict(),
        "reminders": [item.to_dict() for item in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.post("/api/reminders/{patient_id}/{reminder_id}/skip")
async def skip_reminder_task(patient_id: int, reminder_id: int):
    """Mark one reminder task as skipped."""
    reminder = care_service.skip_reminder(patient_id, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminders = care_service.list_reminders(patient_id)
    return {
        "status": "ok",
        "patient_id": patient_id,
        "reminder": reminder.to_dict(),
        "reminders": [item.to_dict() for item in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.get("/api/daily-care/{patient_id}/today")
async def get_daily_care_today(patient_id: str):
    """Return the current daily care loop snapshot."""
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    reminders = care_service.list_reminders(profile.id or 0)
    caregiver_events = caregiver_event_service.list_events(patient_id)
    return care_service.build_daily_care_overview(
        patient_id=patient_id,
        reminders=reminders,
        caregiver_events=caregiver_events,
    )


@app.post("/api/daily-summary/{patient_id}")
async def record_daily_summary(patient_id: str, _: dict = Depends(require_patient_access)):
    """Persist today's caregiver summary for trend views or scheduled jobs."""
    return await daily_summary_service.record_today(patient_id)


@app.get("/api/daily-summary/{patient_id}")
async def get_daily_summary_trend(patient_id: str, days: int = 14, _: dict = Depends(require_patient_access)):
    """Return cross-day caregiver summary trend records."""
    return await daily_summary_service.get_trend(patient_id, days=days)


@app.get("/api/consent/{patient_id}")
async def get_consent_record(patient_id: str):
    """Check whether a patient has completed informed consent."""
    record = consent_service.get_consent(patient_id)
    return {
        "consented": bool(record.get("consented")),
        "consent_time": record.get("consent_time", ""),
    }


@app.post("/api/consent/{patient_id}")
async def record_consent(patient_id: str, data: ConsentRequest, request: Request):
    """Record caregiver informed consent without updating existing records."""
    try:
        return consent_service.record_consent(
            patient_id=patient_id,
            consented_by=data.consented_by,
            consent_version=data.consent_version,
            ip_address=request.client.host if request.client else "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/caregivers")
async def api_list_caregivers(_: dict = Depends(require_owner)):
    """返回当前所有启用中的照护者，供 owner 管理团队。"""
    return {"caregivers": await auth_service.list_caregivers()}


@app.post("/api/caregivers")
async def api_create_caregiver(data: CaregiverCreateRequest, _: dict = Depends(require_owner)):
    """新增一位协作照护者，并可选授予当前患者访问权限。"""
    try:
        caregiver = await auth_service.create_caregiver(
            name=data.name,
            pin=data.pin,
            role=data.role,
            patient_id=data.patient_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "caregiver": caregiver}


@app.put("/api/caregivers/{caregiver_id}/pin")
async def api_update_caregiver_pin(
    caregiver_id: str,
    data: CaregiverPinUpdateRequest,
    current_caregiver: dict = Depends(get_current_caregiver),
):
    """本人改 PIN 需要旧 PIN；owner 可直接重置他人 PIN。"""
    target_id = str(caregiver_id or "").strip()
    current_id = str(current_caregiver.get("id") or "")
    is_self = target_id == current_id
    is_owner = str(current_caregiver.get("role") or "") == "owner"
    if not is_self and not is_owner:
        raise HTTPException(status_code=403, detail="无权修改该照护者 PIN")
    if not await auth_service.get_caregiver(target_id):
        raise HTTPException(status_code=404, detail="照护者不存在")
    if is_self:
        if not data.old_pin or not await auth_service.verify_pin(current_id, data.old_pin):
            raise HTTPException(status_code=400, detail="旧 PIN 不正确")
    try:
        await auth_service.update_pin(target_id, data.new_pin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.put("/api/caregivers/{id}/pin")
async def api_update_caregiver_pin_by_id(
    id: str,
    data: CaregiverPinUpdateRequest,
    current_caregiver: dict = Depends(get_current_caregiver),
):
    """兼容旧前端/验证脚本使用的 id 路径参数。"""
    return await api_update_caregiver_pin(id, data, current_caregiver)


@app.delete("/api/caregivers/{caregiver_id}")
async def api_delete_caregiver(
    caregiver_id: str,
    current_caregiver: dict = Depends(require_owner),
):
    """软删除协作照护者。"""
    target_id = str(caregiver_id or "").strip()
    if target_id == str(current_caregiver.get("id") or ""):
        raise HTTPException(status_code=400, detail="不能停用当前登录中的照护者")
    if not await auth_service.get_caregiver(target_id):
        raise HTTPException(status_code=404, detail="照护者不存在")
    try:
        await auth_service.deactivate_caregiver(target_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True}


@app.get("/api/settings/ollama-status")
async def api_ollama_status(_: dict = Depends(get_current_caregiver)):
    """返回本地 Ollama 运行状态。"""
    runtime = local_llm_service.get_runtime_config()
    return {
        "available": await local_llm_service.is_ollama_available(),
        "model": runtime["model"],
        "base_url": runtime["base_url"],
        "enabled": runtime["enabled"],
    }


@app.put("/api/settings/llm-mode")
async def api_update_llm_mode(data: LocalLLMModeRequest, _: dict = Depends(get_current_caregiver)):
    """动态切换本地优先模式，只影响当前进程。"""
    local_llm_service.set_local_enabled(data.local_enabled)
    return {
        "ok": True,
        "current_mode": "local" if local_llm_service.is_local_enabled() else "api",
    }


@app.get("/api/settings/storage-info")
async def api_storage_info(_: dict = Depends(get_current_caregiver)):
    """返回 SQLite 与 Chroma 本地存储信息。"""
    db_size_mb = round((DB_PATH.stat().st_size / (1024 * 1024)), 2) if DB_PATH.exists() else 0.0
    chroma_path = memory_vector_service.CHROMA_DIR
    return {
        "db_size_mb": db_size_mb,
        "db_path": str(DB_PATH),
        "chroma_path": str(chroma_path),
        "chroma_entries": memory_vector_service.get_chroma_entry_count(),
    }


@app.post("/api/settings/clear-cache")
async def api_clear_cache(_: dict = Depends(get_current_caregiver)):
    """一键清空 Chroma 向量缓存，不删除 SQLite 主库。"""
    memory_vector_service.clear_chroma_cache()
    return {"ok": True}


@app.post("/api/settings/clear-pwa-cache")
async def api_clear_pwa_cache(_: dict = Depends(get_current_caregiver)):
    """提示前端清理浏览器侧 PWA/Service Worker 缓存。"""
    return {"ok": True, "message": "请在浏览器中手动清除 Service Worker 缓存"}


@app.post("/api/settings/test-notify")
async def api_test_notify(_: dict = Depends(get_current_caregiver)):
    """发送一条外部通知测试消息。"""
    ok = await notify_service.send_notify("测试", "✅ 系统通知测试成功")
    return {
        "ok": ok,
        "message": "测试消息已发送" if ok else "未发送：Webhook 未配置或发送失败",
    }


@app.put("/api/settings/notify-webhook")
async def api_update_notify_webhook(data: NotifyWebhookRequest, _: dict = Depends(get_current_caregiver)):
    """动态更新通知 webhook，只影响当前进程。"""
    notify_service.set_webhook(data.url, data.type)
    return {
        "ok": True,
        "configured": bool(notify_service.get_webhook_url()),
        "type": notify_service.get_webhook_type(),
    }


@app.get("/event_logs")
async def get_event_logs(user_profile_id: int | None = None, limit: int = 30):
    """Return recent caregiver event logs."""
    profile = _resolve_profile_for_care(user_profile_id)
    events = care_service.list_event_logs(profile.id or 0, limit=limit)
    return {
        "profile": profile.to_dict(),
        "event_logs": [event.to_dict() for event in events],
    }


@app.post("/event_logs")
async def create_event_log(data: EventLogRequest):
    """Create a caregiver event log."""
    profile = _resolve_profile_for_care(data.user_profile_id)
    event = care_service.create_event_log(profile.id or 0, data.model_dump())
    events = care_service.list_event_logs(profile.id or 0)
    return {
        "status": "ok",
        "profile": profile.to_dict(),
        "event": event.to_dict(),
        "event_logs": [item.to_dict() for item in events],
    }


@app.get("/caregivers")
async def get_caregiver_links(user_profile_id: int | None = None):
    """Return lightweight caregiver collaboration links."""
    profile = _resolve_profile_for_care(user_profile_id)
    caregivers = care_service.list_caregiver_links(profile.id or 0)
    return {
        "profile": profile.to_dict(),
        "caregiver_links": [caregiver.to_dict() for caregiver in caregivers],
    }


@app.get("/api/materials/{patient_id}/timeline")
async def get_materials_timeline(patient_id: str, _: dict = Depends(require_patient_access)):
    """返回指定患者的家庭记忆相册，按年代分组。"""
    patient = await patient_service.get_patient(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return familiar_material_service.grouped_timeline(patient_id)


async def _ensure_material_access(material_id: int, current_caregiver: dict) -> object:
    """确认当前照护者可以操作该素材；老版本整型 profile 素材保持兼容。"""
    material = familiar_material_service.get_material_by_id(material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Familiar material not found")
    patient_id = str(material.patient_id)
    if str(current_caregiver.get("role") or "") == "owner":
        return material
    if await auth_service.check_access(str(current_caregiver.get("id") or ""), patient_id):
        return material
    raise HTTPException(status_code=403, detail="无权操作该素材")


@app.post("/api/materials/{material_id}/voice-note")
async def upload_material_voice_note(
    material_id: int,
    request: Request,
    current_caregiver: dict = Depends(get_current_caregiver),
):
    """保存照护者录制的照片语音说明，供家庭记忆相册播放。"""
    material = await _ensure_material_access(material_id, current_caregiver)
    try:
        body = await request.body()
        _filename, audio_bytes, _content_type = _extract_audio_upload(request, body)
        voice_dir = STATIC_DIR / "voice_notes"
        voice_dir.mkdir(parents=True, exist_ok=True)
        output_name = f"{material.patient_id}_{material_id}.webm"
        output_path = voice_dir / output_name
        output_path.write_bytes(audio_bytes)
        public_path = f"/static/voice_notes/{output_name}"
        updated = familiar_material_service.update_voice_note_path(material_id, public_path)
        return {"ok": True, "material": updated.to_dict() if updated else None, "voice_note_path": public_path}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"语音说明保存失败: {exc}") from exc


@app.put("/api/materials/{material_id}")
async def update_material_timeline(
    material_id: int,
    data: dict,
    current_caregiver: dict = Depends(get_current_caregiver),
):
    """只更新时间线增强字段，避免覆盖素材库主表单中的旧字段。"""
    await _ensure_material_access(material_id, current_caregiver)
    material = familiar_material_service.update_timeline_fields(material_id, data or {})
    if material is None:
        raise HTTPException(status_code=404, detail="Familiar material not found")
    return {"ok": True, "material": material.to_dict()}


@app.get("/api/materials/{patient_id}")
async def get_familiar_materials(patient_id: str):
    """Return familiar materials for one patient/profile id."""
    profile = profile_service.get_profile_by_id(int(patient_id)) if str(patient_id).isdigit() else None
    patient = await patient_service.get_patient(patient_id) if profile is None else None
    if profile is None and patient is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    materials = familiar_material_service.list_materials(patient_id)
    return {
        "profile": profile.to_dict() if profile else _patient_to_companion_profile(patient).to_dict(),
        "materials": [material.to_dict() for material in materials],
        "status": familiar_material_service.summarize_status(materials),
        "type_labels": familiar_material_service.TYPE_LABELS,
    }


@app.post("/api/materials/{patient_id}")
async def create_familiar_material(patient_id: str, data: FamiliarMaterialRequest):
    """Create one familiar material."""
    profile = profile_service.get_profile_by_id(int(patient_id)) if str(patient_id).isdigit() else None
    patient = await patient_service.get_patient(patient_id) if profile is None else None
    if profile is None and patient is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    material = familiar_material_service.save_material(patient_id, data.model_dump())
    materials = familiar_material_service.list_materials(patient_id)
    return {
        "status": "ok",
        "profile": profile.to_dict() if profile else _patient_to_companion_profile(patient).to_dict(),
        "material": material.to_dict(),
        "materials": [item.to_dict() for item in materials],
        "material_status": familiar_material_service.summarize_status(materials),
    }


@app.put("/api/materials/{patient_id}/{material_id}")
async def update_familiar_material(patient_id: str, material_id: int, data: FamiliarMaterialRequest):
    """Update one familiar material."""
    if familiar_material_service.get_material_or_404(patient_id, material_id) is None:
        raise HTTPException(status_code=404, detail="Familiar material not found")
    material = familiar_material_service.save_material(patient_id, data.model_dump(), material_id=material_id)
    materials = familiar_material_service.list_materials(patient_id)
    return {
        "status": "ok",
        "material": material.to_dict(),
        "materials": [item.to_dict() for item in materials],
        "material_status": familiar_material_service.summarize_status(materials),
    }


@app.delete("/api/materials/{patient_id}/{material_id}")
async def delete_familiar_material(patient_id: str, material_id: int):
    """Delete one familiar material."""
    if not familiar_material_service.delete_material(patient_id, material_id):
        raise HTTPException(status_code=404, detail="Familiar material not found")
    materials = familiar_material_service.list_materials(patient_id)
    return {
        "status": "ok",
        "materials": [item.to_dict() for item in materials],
        "material_status": familiar_material_service.summarize_status(materials),
    }


@app.get("/api/memory-candidates/{patient_id}")
async def get_memory_candidates(patient_id: int, _: dict = Depends(get_current_caregiver)):
    """Return caregiver-reviewed memory candidates."""
    profile = profile_service.get_profile_by_id(patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    candidates = memory_candidate_service.list_candidates(patient_id, limit=100)
    return {
        "profile": profile.to_dict(),
        "candidates": [candidate.to_dict() for candidate in candidates],
        "type_labels": memory_candidate_service.TYPE_LABELS,
    }


@app.get("/api/memories/search")
async def search_memories(query: str, patient_id: str, _: dict = Depends(require_patient_access), top_k: int = 4):
    """按语义检索某位患者最相关的已审批记忆，不改动现有聊天主链路。"""
    try:
        results = await memory_vector_service.search_memory(
            query=query,
            patient_id=patient_id,
            top_k=top_k or 4,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "query": query,
        "patient_id": patient_id,
        "top_k": top_k or 4,
        "results": results,
    }


@app.get("/api/memories/{patient_id}/by-category")
async def get_memories_by_category(patient_id: str, _: dict = Depends(require_patient_access)):
    """按分类返回某位患者的已审批记忆，供追忆页导航使用。"""
    try:
        return await memory_vector_service.get_memories_by_category(patient_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/memory-candidates/{patient_id}")
async def create_memory_candidate(patient_id: int, data: MemoryCandidateRequest, _: dict = Depends(get_current_caregiver)):
    """Create one memory candidate manually."""
    profile = profile_service.get_profile_by_id(patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    payload = data.model_dump()
    # 保存前做软性去重/冲突检测；检测失败不阻断照护者后续审核。
    candidate_text = "；".join(
        part
        for part in (
            payload.get("suggested_title", ""),
            payload.get("suggested_description", ""),
            payload.get("source_message", ""),
        )
        if str(part or "").strip()
    )
    duplicate_result, conflict_result = await asyncio.gather(
        memory_dedup_service.check_duplicate(candidate_text, str(patient_id)),
        memory_dedup_service.check_conflict(candidate_text, str(patient_id)),
        return_exceptions=True,
    )
    if isinstance(duplicate_result, dict) and duplicate_result.get("is_duplicate"):
        payload["dedup_warning"] = (
            f"与已审批记忆相似：{duplicate_result.get('similar_to', '')}"
            f"（score={duplicate_result.get('score', 0)}）"
        )
    if isinstance(conflict_result, dict) and conflict_result.get("conflict"):
        payload["conflict_warning"] = str(conflict_result.get("reason") or "候选记忆与已有记忆存在事实冲突。")

    candidate = memory_candidate_service.create_candidate(patient_id, payload)
    candidates = memory_candidate_service.list_candidates(patient_id, limit=100)
    return {
        "status": "ok",
        "candidate": candidate.to_dict(),
        "candidates": [item.to_dict() for item in candidates],
    }


@app.post("/api/memory-candidates/{patient_id}/{candidate_id}/approve")
async def approve_memory_candidate(
    patient_id: int,
    candidate_id: int,
    data: MemoryCandidateApproveRequest | None = None,
    _: dict = Depends(get_current_caregiver),
):
    """Approve a candidate and add it to familiar materials."""
    profile = profile_service.get_profile_by_id(patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    payload = data.model_dump(exclude_none=True) if data else None
    candidate, material = memory_candidate_service.approve_candidate(
        patient_id,
        candidate_id,
        overrides=payload,
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="Memory candidate not found")
    candidates = memory_candidate_service.list_candidates(patient_id, limit=100)
    materials = familiar_material_service.list_materials(patient_id)
    return {
        "status": "ok",
        "candidate": candidate.to_dict(),
        "material": material,
        "candidates": [item.to_dict() for item in candidates],
        "materials": [item.to_dict() for item in materials],
        "material_status": familiar_material_service.summarize_status(materials),
    }


@app.post("/api/memory-candidates/{patient_id}/{candidate_id}/reject")
async def reject_memory_candidate(patient_id: int, candidate_id: int, _: dict = Depends(get_current_caregiver)):
    """Reject one candidate."""
    profile = profile_service.get_profile_by_id(patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    candidate = memory_candidate_service.reject_candidate(patient_id, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Memory candidate not found")
    candidates = memory_candidate_service.list_candidates(patient_id, limit=100)
    return {
        "status": "ok",
        "candidate": candidate.to_dict(),
        "candidates": [item.to_dict() for item in candidates],
    }


@app.get("/api/caregiver/{patient_id}/events")
async def get_caregiver_events(patient_id: str, limit: int = 30):
    """Return recent rule-triggered caregiver insight events."""
    events = caregiver_event_service.list_events(patient_id, limit=limit)
    if not events and patient_id == "demo_patient_001":
        return {
            "patient_id": patient_id,
            "events": caregiver_event_service.demo_summary()["top_events"],
            "demo": True,
        }
    return {
        "patient_id": patient_id,
        "events": [event.to_dict() for event in events],
        "demo": False,
    }


@app.get("/api/caregiver/{patient_id}/summary")
async def get_caregiver_summary(patient_id: str):
    """Return a caregiver-facing risk and action summary."""
    patient = await patient_service.get_patient(patient_id)
    patient_name = "李奶奶" if patient_id == "demo_patient_001" else (patient.get("name") if patient else patient_id)
    summary = caregiver_event_service.build_summary(
        patient_id,
        patient_name=str(patient_name or patient_id),
    )
    if not summary["top_events"] and patient_id == "demo_patient_001":
        return caregiver_event_service.demo_summary()
    return summary


@app.post("/api/caregiver/{patient_id}/events/{event_id}/resolve")
async def resolve_caregiver_event(patient_id: str, event_id: str):
    """Resolve one caregiver insight event."""
    event = caregiver_event_service.resolve_event(patient_id, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Caregiver event not found")
    return {
        "status": "ok",
        "event": event.to_dict(),
        "summary": caregiver_event_service.build_summary(patient_id),
    }


@app.get("/api/debug/llm-status")
async def get_debug_llm_status():
    """Return current provider status without exposing API keys."""
    return llm_service.get_llm_runtime_status()


@app.get("/api/debug/last-chat")
async def get_debug_last_chat():
    """Return the latest in-process chat diagnostics."""
    diagnostics = chat_service.get_last_chat_diagnostics()
    return {
        "has_chat": bool(diagnostics),
        "diagnostics": diagnostics,
    }


@app.get("/api/debug/test-results")
async def get_debug_test_results(include_markdown: bool = True):
    """Return report file status and parsed JSON metrics."""
    return _build_test_results_payload(include_markdown=include_markdown)


@app.post("/caregivers")
async def create_caregiver_link(data: CaregiverLinkRequest):
    """Create a lightweight caregiver collaboration link."""
    profile = _resolve_profile_for_care(data.user_profile_id)
    caregiver = care_service.create_caregiver_link(profile.id or 0, data.model_dump())
    caregivers = care_service.list_caregiver_links(profile.id or 0)
    return {
        "status": "ok",
        "profile": profile.to_dict(),
        "caregiver": caregiver.to_dict(),
        "caregiver_links": [item.to_dict() for item in caregivers],
    }


@app.post("/chat")
async def chat(data: ChatRequest):
    """Generate a reply using the saved profile, recent logs, and mode prompt."""
    requested_patient_id = str(data.patient_id or "").strip()
    selected_patient = await patient_service.get_patient(requested_patient_id) if requested_patient_id else None

    if selected_patient and requested_patient_id != "demo_patient_001":
        patient_profile = _patient_to_companion_profile(selected_patient)
        conversation = llm_service.LLMConversationInput(
            system_prompt="请根据当前患者档案和已确认记忆，进行温和、简短的陪伴对话。",
            support_mode=data.mode or "alzheimer",
            profile=patient_profile,
            recent_logs=[],
            user_message=data.message,
            context_text="",
            memory_summary="",
            patient_id=requested_patient_id,
        )
        llm_result = llm_service.get_llm_service().generate_reply_result(conversation)
        result = {
            "reply": llm_result.reply,
            "profile": patient_profile.to_dict(),
            "mode": data.mode or "alzheimer",
            "analysis": {},
            "mode_meta": chat_service.get_support_meta(),
            "logs": [],
            "memory_digest": {},
            "diagnostics": {
                "requested_provider": llm_result.requested_provider,
                "actual_provider": llm_result.actual_provider,
                "model": llm_result.model,
                "fallback_used": llm_result.fallback_used,
                "fallback_reason": llm_result.fallback_reason,
                "postprocess_used": llm_result.postprocess_used,
                "template_used": llm_result.template_used,
                "hallucination_warning": llm_result._hallucination_warning,
            },
            "caregiver_events": [],
            "debug": {},
        }
    else:
        try:
            result = chat_service.generate_chat_reply(
                user_id=data.user_id,
                message=data.message,
                mode=data.mode,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    profile_payload = result.get("profile") or {}
    profile_name = str(profile_payload.get("name") or "")
    profile_id = profile_payload.get("id") or data.user_id or 0
    patient_id = requested_patient_id or ("demo_patient_001" if profile_name in {"李奶奶", "李桂兰"} else f"profile_{profile_id}")
    session_id = str(data.session_id or "").strip() or f"{patient_id}-{uuid.uuid4()}"
    try:
        user_profile_id = int(profile_id) if profile_id else None
    except (TypeError, ValueError):
        user_profile_id = None
    asyncio.create_task(_analyze_and_update_daily_mood(data.message, patient_id))
    asyncio.create_task(
        _score_and_record_chat_turn(
            user_message=data.message,
            assistant_response=str(result["reply"]),
            patient_id=patient_id,
            session_id=session_id,
            user_profile_id=user_profile_id,
        )
    )
    asyncio.create_task(
        _analyze_and_record_risk(
            user_message=data.message,
            assistant_response=str(result["reply"]),
            patient_id=patient_id,
            session_id=session_id,
        )
    )

    return {
        "reply": result["reply"],
        "session_id": session_id,
        "profile": result["profile"],
        "mode": result["mode"],
        "analysis": result["analysis"],
        "mode_meta": result["mode_meta"],
        "logs": result["logs"],
        "memory_digest": result["memory_digest"],
        "diagnostics": result.get("diagnostics"),
        "caregiver_events": result.get("caregiver_events"),
        "debug": result.get("debug"),
    }


@app.post("/voice/transcribe")
async def transcribe_voice(request: Request):
    """Turn one uploaded recording into text without touching the chat core."""
    try:
        result = voice_service.get_voice_service().transcribe_audio(
            filename=request.headers.get("X-Audio-Filename", "recording.webm"),
            audio_bytes=await request.body(),
            content_type=request.headers.get("Content-Type", ""),
        )
    except voice_service.VoiceServiceError as exc:
        payload = exc.to_payload()
        payload["diagnosis"] = diagnostics_service.build_voice_diagnosis(
            stage=exc.stage,
            success=False,
            error_code=exc.error_code,
        ).to_dict()
        return JSONResponse(status_code=exc.status_code, content=payload)

    diagnosis = diagnostics_service.build_voice_diagnosis(
        stage=result.stage,
        success=True,
        error_code=result.error_code,
    ).to_dict()

    return {
        "success": result.success,
        "stage": result.stage,
        "text": result.text,
        "confidence": result.confidence,
        "latency_ms": result.latency_ms,
        "provider": result.provider,
        "model": result.model,
        "error_code": result.error_code,
        "user_friendly_message": result.user_friendly_message,
        "fallback_used": result.fallback_used,
        "diagnosis": diagnosis,
    }


@app.post("/voice/speak")
async def speak_voice(data: VoiceSpeakRequest):
    """Generate spoken audio for one assistant reply."""
    try:
        result = voice_service.get_voice_service().synthesize_speech(text=data.text)
    except voice_service.VoiceServiceError as exc:
        payload = exc.to_payload()
        payload["diagnosis"] = diagnostics_service.build_voice_diagnosis(
            stage=exc.stage,
            success=False,
            error_code=exc.error_code,
        ).to_dict()
        return JSONResponse(status_code=exc.status_code, content=payload)

    diagnosis = diagnostics_service.build_voice_diagnosis(
        stage=result.stage,
        success=True,
        error_code=result.error_code,
    ).to_dict()

    return Response(
        content=result.audio_bytes,
        media_type=result.media_type,
        headers={
            "Cache-Control": "no-store",
            "X-Voice-Provider": result.provider,
            "X-Voice-Model": result.model,
            "X-Voice-Latency-Ms": str(result.latency_ms),
            "X-Voice-Name": result.voice,
            "X-Voice-Fallback-Used": str(result.fallback_used).lower(),
            "X-Voice-Diagnosis-Tags": ",".join(diagnosis["tags"]),
            "X-Voice-Diagnosis-Primary-Issue": str(diagnosis["primary_issue"] or ""),
            "X-Voice-Diagnosis-Severity": str(diagnosis["severity"]),
            "X-Voice-Diagnosis-Human-Summary": str(diagnosis["human_summary"]),
            "X-Voice-Diagnosis-Next-Step": str(diagnosis["suggested_next_step"]),
        },
    )


@app.post("/api/tts/speak")
async def speak_tts(data: TTSSpeakRequest):
    """Return a MiniMax TTS audio URL or a browser-fallback instruction."""
    return tts_service.speak_text(data.text, provider=data.provider)


@app.post("/api/tts")
async def synthesize_tts(data: TTSSpeakRequest):
    """调用 MiniMax TTS；失败时返回 fallback=true 让前端浏览器朗读。"""
    return await tts_service.synthesize(data.text, voice_id=data.voice_id)


@app.post("/api/stt")
async def transcribe_stt(request: Request):
    """接收浏览器录音并调用 OpenAI Whisper 识别文字。"""
    try:
        filename, audio_bytes, content_type = _extract_audio_upload(request, await request.body())
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"text": "", "error": str(exc)})

    try:
        text = await run_in_threadpool(_transcribe_with_whisper, filename, audio_bytes, content_type)
    except RuntimeError as exc:
        return JSONResponse(status_code=503, content={"text": "", "error": str(exc)})
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={"text": "", "error": f"语音识别暂时不可用：{type(exc).__name__}"},
        )

    if not text:
        return JSONResponse(status_code=502, content={"text": "", "error": "没有识别到有效文字，请再试一次。"})
    return {"text": text}


@app.get("/llm_eval/scenarios")
async def get_llm_eval_scenarios():
    """Return preset lab scenarios plus shared restrictions and style hints."""
    return {
        "scenarios": llm_eval_service.list_scenarios(),
        "restricted_words": list(llm_eval_service.RESTRICTED_WORDS),
        "preferred_style_rules": list(llm_eval_service.PREFERRED_STYLE_RULES),
        "provider_availability": asdict(llm_service.get_provider_availability()),
    }


@app.post("/llm_eval/run")
async def run_llm_eval(data: LLMEvalRunRequest):
    """Run one preset Alzheimer companion evaluation scenario."""
    try:
        result = llm_eval_service.run_llm_test_case(
            data.scenario_id,
            provider=data.provider,
            profile_overrides=data.profile.model_dump() if data.profile else None,
            restrictions=data.restrictions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result


@app.post("/llm_eval/custom")
async def run_llm_eval_custom(data: LLMEvalCustomRequest):
    """Run one ad-hoc lab test case against the existing LLM service."""
    try:
        result = llm_eval_service.run_custom_llm_test(
            user_message=data.user_message,
            provider=data.provider,
            speaker=data.speaker,
            title=data.title,
            summary=data.summary,
            risk_focus=data.risk_focus,
            restrictions=data.restrictions,
            profile_overrides=data.profile.model_dump() if data.profile else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result


@app.post("/save_profile")
async def save_profile(data: ProfileRequest):
    """Persist profile data to SQLite so it can be reused across sessions."""
    profile = profile_service.save_profile(data.model_dump())
    return {"status": "ok", "profile": profile.to_dict()}
