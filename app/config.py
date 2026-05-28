"""Centralized project-level display names, UI text, and light env loading."""

from __future__ import annotations

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def load_local_env_file() -> None:
    """Load a local ``.env`` file in the lightest possible way.

    The project still respects real shell environment variables first. This
    helper only fills missing values from ``.env`` so local development can
    copy ``.env.example`` to ``.env`` without extra setup.
    """
    if not ENV_PATH.exists():
        return

    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_key = key.strip()
        normalized_value = value.strip().strip('"').strip("'")
        if normalized_key:
            os.environ.setdefault(normalized_key, normalized_value)


load_local_env_file()

PROJECT_NAME = "LLM-Assisted Companion and Caregiving Support System"
PAGE_TITLE = "面向阿尔兹海默症家庭的陪伴与照护辅助系统"
PAGE_EYEBROW = "陪伴与照护辅助系统"

SUPPORT_MODE = "alzheimer"
SUPPORT_MODE_LABEL = "阿尔兹海默症陪伴支持"
SUPPORT_MODE_DESCRIPTION = "围绕熟悉的人、地方和往事慢慢展开，帮助陪伴与温和回忆。"
