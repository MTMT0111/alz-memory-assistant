#!/usr/bin/env python3
"""Smoke test the LLM scenario evaluation page API."""

from __future__ import annotations

import os
import sys
import importlib.util
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("LLM_TIMEOUT_SECONDS", "8")

from app.config import load_local_env_file

load_local_env_file()

from app.main import LLMEvalRunRequest, get_llm_eval_scenarios, run_llm_eval


def _load_seed_demo_patient():
    module_path = PROJECT_ROOT / "scripts" / "seed_demo_patient.py"
    spec = importlib.util.spec_from_file_location("project_seed_demo_patient", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/seed_demo_patient.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.seed_demo_patient


seed_demo_patient = _load_seed_demo_patient()


REQUIRED_PROVIDER_FIELDS = {
    "requested_provider",
    "actual_provider",
    "model",
    "fallback_used",
    "fallback_reason",
    "postprocess_used",
    "template_used",
    "template_name",
    "detected_state",
    "strategy",
    "response_time_ms",
}

REQUIRED_EVALUATION_FIELDS = {
    "is_short_sentence",
    "is_warm",
    "has_forbidden_words",
    "direct_patient_stimulation",
    "medication_hallucination",
    "unsafe_wandering_encouragement",
    "used_profile",
    "used_familiar_materials",
    "quality_score",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def _run_case(scenario_id: str, provider: str) -> dict:
    data = await run_llm_eval(LLMEvalRunRequest(scenario_id=scenario_id, provider=provider))
    provider_meta = data.get("provider") or {}
    evaluation = data.get("evaluation") or {}
    missing_provider = REQUIRED_PROVIDER_FIELDS.difference(provider_meta)
    missing_eval = REQUIRED_EVALUATION_FIELDS.difference(evaluation)
    _assert(not missing_provider, f"{scenario_id} missing provider fields: {sorted(missing_provider)}")
    _assert(not missing_eval, f"{scenario_id} missing evaluation fields: {sorted(missing_eval)}")
    _assert(data.get("raw_llm_reply") is not None, f"{scenario_id} missing raw_llm_reply")
    _assert(data.get("safe_template_reply") is not None, f"{scenario_id} missing safe_template_reply")
    _assert(data.get("final_assistant_reply"), f"{scenario_id} missing final_assistant_reply")
    return data


async def _run_checks() -> None:
    scenarios_payload = await get_llm_eval_scenarios()
    scenarios = scenarios_payload.get("scenarios") or []
    scenario_ids = {item.get("id") for item in scenarios}
    _assert("reminiscence_old_work" in scenario_ids, "reminiscence scenario is missing")
    _assert("deceased_relative" in scenario_ids, "deceased-relative scenario is missing")

    deepseek_case = await _run_case("reminiscence_old_work", "deepseek")
    deepseek_meta = deepseek_case.get("provider") or {}
    _assert(
        deepseek_meta.get("requested_provider") == "deepseek",
        "scene eval did not request DeepSeek",
    )
    _assert(
        deepseek_meta.get("actual_provider") in {"deepseek", "template_fallback", "mock"},
        f"unexpected actual provider: {deepseek_meta.get('actual_provider')}",
    )
    if deepseek_meta.get("actual_provider") != "deepseek":
        _assert(deepseek_meta.get("fallback_reason"), "DeepSeek fallback must include fallback_reason")

    high_risk_case = await _run_case("deceased_relative", "mock")
    high_risk_meta = high_risk_case.get("provider") or {}
    _assert(
        high_risk_meta.get("actual_provider") == "template_fallback",
        "deceased-relative high-risk case must use template_fallback",
    )
    _assert(high_risk_meta.get("template_used") is True, "high-risk template_used should be true")

    mock_case = await _run_case("fear_anxiety", "mock")
    mock_reply = mock_case.get("final_assistant_reply") or ""
    bad_mock_markers = ("模拟回复", "mock reply", "lorem ipsum", "TODO")
    _assert(not any(marker in mock_reply for marker in bad_mock_markers), "mock provider returned a meaningless placeholder")


def main() -> int:
    print("LLM scenario eval page smoke test")
    seed_demo_patient()
    asyncio.run(_run_checks())

    print("PASS: LLM scenario eval page diagnostics and safety fallback are working.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
