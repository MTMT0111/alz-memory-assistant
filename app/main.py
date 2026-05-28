"""FastAPI entry point for the Alzheimer companion and memory assistant."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.config import PAGE_EYEBROW, PAGE_TITLE
from app.init_db import initialize_database
from app.routes.location import router as location_router
from app.services import analysis_service, app_summary_service, care_service, caregiver_event_service, chat_service, diagnostics_service, familiar_material_service, llm_eval_service, llm_service, memory_candidate_service, profile_service, tts_service, voice_service

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepare the SQLite database before the app starts serving requests."""
    initialize_database()
    llm_service.log_llm_runtime_config_once(force=True)
    yield


app = FastAPI(
    title=PAGE_TITLE,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(location_router)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

PAGE_NAV_META = {
    "conversation": {"title": "Patient Mode", "subtitle": "Voice-first companion", "role_label": "Patient"},
    "dashboard": {"title": "Caregiver Workspace", "subtitle": "Care overview", "role_label": "Caregiver"},
    "profile": {"title": "Profile", "subtitle": "Family memory profile", "role_label": "Caregiver"},
    "notes": {"title": "Care Notes", "subtitle": "Recent summaries and events", "role_label": "Caregiver"},
    "analysis": {"title": "Weekly Analysis", "subtitle": "Conversation and care trends", "role_label": "Caregiver"},
    "device": {"title": "Settings", "subtitle": "Reminders and voice preferences", "role_label": "Caregiver"},
    "safety": {"title": "Safety", "subtitle": "Location and wandering support", "role_label": "Caregiver"},
    "llm_eval": {"title": "LLM Eval", "subtitle": "Developer-side quality checks", "role_label": "Caregiver"},
    "debug_dashboard": {"title": "Model Status", "subtitle": "Provider and test visibility", "role_label": "Debug"},
    "test_results": {"title": "Test Results", "subtitle": "Reports and quality checks", "role_label": "Debug"},
    "materials": {"title": "Materials", "subtitle": "Familiar cues and family media", "role_label": "Caregiver"},
    "chat_history": {"title": "Chat History", "subtitle": "Recent dialogue and memory candidates", "role_label": "Caregiver"},
    "reminiscence": {"title": "Reminiscence", "subtitle": "Familiar materials for gentle recall", "role_label": "Caregiver"},
    "app_home": {"title": "App Home", "subtitle": "Companion and caregiving support", "role_label": "App"},
    "demo_flow": {"title": "Demo Flow", "subtitle": "Stable showcase steps", "role_label": "Demo"},
    "login": {"title": "Welcome", "subtitle": "Mock app sign in", "role_label": "Demo"},
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


class VoiceSpeakRequest(BaseModel):
    """Request body for generating a spoken assistant reply."""

    text: str = Field(min_length=1)


class TTSSpeakRequest(BaseModel):
    """Request body for MiniMax/browser TTS orchestration."""

    text: str = Field(min_length=1)
    provider: str = "minimax"


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
    caregiver_patient_id = "demo_patient_001" if profile.name in {"李奶奶", "李桂兰"} else f"profile_{profile.id or 0}"
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
        "mock_user": demo_user,
        "shell_meta": nav_meta,
        "shell_status": shell_status,
        "debug_mode": request.query_params.get("debug") == "1",
    }


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


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Send the default entry straight to the companion conversation page."""
    return RedirectResponse(url="/conversation", status_code=307)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render a lightweight mock login and role selection page."""
    demo_user = request.query_params.get("user", "").strip()
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=_build_page_context(
            request,
            active_page="login",
            recent_limit=2,
            app_role="guest",
            page_title_override=f"{PAGE_TITLE} · Login",
            mock_user=demo_user,
        ),
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


@app.get("/care-portal", response_class=HTMLResponse)
async def care_portal_page(request: Request):
    """Render the support-side overview page for family and settings access."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_build_page_context(
            request,
            active_page="dashboard",
            recent_limit=8,
            app_role="caregiver",
        ),
    )


@app.get("/conversation", response_class=HTMLResponse)
async def conversation_page(request: Request):
    """Render the focused chat page."""
    return templates.TemplateResponse(
        request=request,
        name="conversation.html",
        context=_build_page_context(
            request,
            active_page="conversation",
            recent_limit=10,
            app_role="patient",
        ),
    )


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
            page_title_override="李奶奶熟悉素材库",
        ),
    )


@app.get("/chat-history", response_class=HTMLResponse)
async def chat_history_page(request: Request):
    """Render recent chat logs grouped by date with memory candidates."""
    context = _build_page_context(
        request,
        active_page="chat_history",
        recent_limit=50,
        app_role="caregiver",
        page_title_override="李奶奶聊天记录与记忆候选",
    )
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    logs = chat_service.get_recent_chat_logs(profile.id, limit=50, mode=profile.support_mode)
    context["chat_history_groups"] = _build_chat_history_groups(logs)
    context["memory_candidates"] = [candidate.to_dict() for candidate in memory_candidate_service.list_candidates(profile.id or 0, limit=30)]
    return templates.TemplateResponse(
        request=request,
        name="chat_history.html",
        context=context,
    )


@app.get("/reminiscence", response_class=HTMLResponse)
async def reminiscence_page(request: Request):
    """Render familiar materials as a lightweight reminiscence companion page."""
    context = _build_page_context(
        request,
        active_page="reminiscence",
        recent_limit=8,
        app_role="caregiver",
        page_title_override="李奶奶的回忆陪伴",
    )
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    materials = familiar_material_service.list_materials(profile.id or 0)
    context["materials_by_type"] = _group_materials_by_type(materials)
    context["material_type_labels"] = familiar_material_service.TYPE_LABELS
    return templates.TemplateResponse(
        request=request,
        name="reminiscence.html",
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
async def get_reminder_tasks(patient_id: int):
    """Return structured reminder tasks for one patient."""
    reminders = care_service.list_reminders(patient_id)
    return {
        "patient_id": patient_id,
        "reminders": [reminder.to_dict() for reminder in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
    }


@app.post("/api/reminders/{patient_id}")
async def create_reminder_task(patient_id: int, data: ReminderRequest):
    """Create or update one structured reminder task."""
    reminder = care_service.save_reminder(patient_id, data.model_dump())
    reminders = care_service.list_reminders(patient_id)
    return {
        "status": "ok",
        "patient_id": patient_id,
        "reminder": reminder.to_dict(),
        "reminders": [item.to_dict() for item in reminders],
        "status_summary": care_service.build_reminder_status_summary(reminders),
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


@app.get("/api/materials/{patient_id}")
async def get_familiar_materials(patient_id: int):
    """Return familiar materials for one patient profile."""
    profile = profile_service.get_profile_by_id(patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    materials = familiar_material_service.list_materials(patient_id)
    return {
        "profile": profile.to_dict(),
        "materials": [material.to_dict() for material in materials],
        "status": familiar_material_service.summarize_status(materials),
        "type_labels": familiar_material_service.TYPE_LABELS,
    }


@app.post("/api/materials/{patient_id}")
async def create_familiar_material(patient_id: int, data: FamiliarMaterialRequest):
    """Create one familiar material."""
    profile = profile_service.get_profile_by_id(patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    material = familiar_material_service.save_material(patient_id, data.model_dump())
    materials = familiar_material_service.list_materials(patient_id)
    return {
        "status": "ok",
        "profile": profile.to_dict(),
        "material": material.to_dict(),
        "materials": [item.to_dict() for item in materials],
        "material_status": familiar_material_service.summarize_status(materials),
    }


@app.put("/api/materials/{patient_id}/{material_id}")
async def update_familiar_material(patient_id: int, material_id: int, data: FamiliarMaterialRequest):
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
async def delete_familiar_material(patient_id: int, material_id: int):
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
async def get_memory_candidates(patient_id: int):
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


@app.post("/api/memory-candidates/{patient_id}")
async def create_memory_candidate(patient_id: int, data: MemoryCandidateRequest):
    """Create one memory candidate manually."""
    profile = profile_service.get_profile_by_id(patient_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    candidate = memory_candidate_service.create_candidate(patient_id, data.model_dump())
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
async def reject_memory_candidate(patient_id: int, candidate_id: int):
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
    profile = profile_service.get_latest_profile() or profile_service.ensure_default_profile()
    patient_name = "李奶奶" if patient_id == "demo_patient_001" else (profile.name or "李奶奶")
    summary = caregiver_event_service.build_summary(
        patient_id,
        patient_name=patient_name,
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
    try:
        result = chat_service.generate_chat_reply(
            user_id=data.user_id,
            message=data.message,
            mode=data.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "reply": result["reply"],
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
