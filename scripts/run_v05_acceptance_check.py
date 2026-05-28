#!/usr/bin/env python3
"""Run the v0.5 stability acceptance checks with per-step timeouts."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8001").rstrip("/")
SERVER_HINT = (
    "请先启动：\n"
    "venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"
)


@dataclass(frozen=True)
class Check:
    name: str
    command: list[str]
    timeout_seconds: int
    needs_server: bool = False


def _env_for_check(check: Check) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("BASE_URL", DEFAULT_BASE_URL)
    env.setdefault("CHAT_URL", f"{DEFAULT_BASE_URL}/chat")
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def _run_check(check: Check) -> dict[str, object]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            check.command,
            cwd=PROJECT_ROOT,
            env=_env_for_check(check),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=check.timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - started
        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
        status = "PASS" if completed.returncode == 0 else "FAIL"
        reason = output or f"exit code {completed.returncode}"
        if completed.returncode != 0 and check.needs_server:
            lowered = output.lower()
            if completed.returncode == 2 or "connection refused" in lowered or "cannot connect" in lowered or "无法连接" in output:
                reason = f"{reason}\n\n{SERVER_HINT}"
        return {
            "name": check.name,
            "status": status,
            "duration": duration,
            "reason": reason,
        }
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        output = "\n".join(
            part.decode("utf-8", errors="replace") if isinstance(part, bytes) else str(part)
            for part in (exc.stdout, exc.stderr)
            if part
        ).strip()
        reason = f"timeout after {check.timeout_seconds}s"
        if output:
            reason = f"{reason}\n{output}"
        return {
            "name": check.name,
            "status": "FAIL",
            "duration": duration,
            "reason": reason,
        }


def main() -> int:
    python = sys.executable
    checks = [
        Check("compileall app scripts", [python, "-m", "compileall", "app", "scripts"], 120),
        Check("seed_demo_patient.py", [python, "scripts/seed_demo_patient.py"], 60),
        Check("test_page_chat_deepseek.py", [python, "scripts/test_page_chat_deepseek.py"], 150, needs_server=True),
        Check("test_daily_care_loop.py", [python, "scripts/test_daily_care_loop.py"], 120),
        Check("test_memory_candidate_flow.py", [python, "scripts/test_memory_candidate_flow.py"], 120),
        Check("test_demo_flow_page.py", [python, "scripts/test_demo_flow_page.py"], 60, needs_server=True),
        Check("test_reminder_status.py", [python, "scripts/test_reminder_status.py"], 120),
        Check("test_tts_service.py", [python, "scripts/test_tts_service.py"], 90),
        Check("evaluate_controlled_llm_comparison.py", [python, "scripts/evaluate_controlled_llm_comparison.py"], 600),
    ]

    print("v0.5 acceptance check")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"BASE_URL: {DEFAULT_BASE_URL}")
    print()

    results = []
    for check in checks:
        print(f"RUN  {check.name} (timeout={check.timeout_seconds}s)")
        result = _run_check(check)
        results.append(result)
        print(f"{result['status']} {check.name} ({float(result['duration']):.1f}s)")
        if result["status"] != "PASS":
            print("Reason:")
            print(result["reason"])
        print("-" * 72)

    passed = sum(1 for result in results if result["status"] == "PASS")
    failed = len(results) - passed
    print("Final summary")
    print(f"PASS: {passed}")
    print(f"FAIL: {failed}")
    print(f"TOTAL: {len(results)}")
    if failed:
        print()
        print("Failed checks:")
        for result in results:
            if result["status"] != "PASS":
                print(f"- {result['name']} ({float(result['duration']):.1f}s)")
        print()
        print("If HTTP page/API checks failed because the service is unavailable:")
        print(SERVER_HINT)
        return 1
    print("All v0.5 acceptance checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
