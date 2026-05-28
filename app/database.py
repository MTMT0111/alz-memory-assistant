"""SQLite connection helpers shared across services."""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Resolve the repository root once so every module writes to the same database file.
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


def ensure_data_dir() -> Path:
    """Create the persistent data directory when the app boots for the first time."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def get_connection() -> sqlite3.Connection:
    """Return a fresh SQLite connection configured for row-style access."""
    ensure_data_dir()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection
