"""Database initialization for the companion assistant."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime

from app.database import DB_PATH, get_connection
from app.services import familiar_material_service
from app.services.profile_service import ensure_default_profile

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    hometown TEXT,
    support_mode TEXT NOT NULL,
    family_info TEXT,
    life_events TEXT,
    preferences TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    relation TEXT,
    avatar_emoji TEXT DEFAULT '👵',
    stage TEXT DEFAULT '轻度',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1
);

INSERT OR IGNORE INTO patients (id, name, age, relation, stage)
VALUES ('demo_patient_001', '示例患者', 78, '母亲', '中度');

CREATE TABLE IF NOT EXISTS caregivers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    role TEXT DEFAULT 'member',
    avatar_emoji TEXT DEFAULT '👤',
    created_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS caregiver_patient_access (
    caregiver_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    granted_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (caregiver_id, patient_id)
);

INSERT OR IGNORE INTO caregivers (id, name, pin_hash, role)
VALUES (
    'default_caregiver',
    '主照护者',
    '9af15b336e6a9619928537df30b2e6a2376569fcf9d7e773eccede65606529a0',
    'owner'
);

INSERT OR IGNORE INTO caregiver_patient_access (caregiver_id, patient_id)
SELECT 'default_caregiver', id FROM patients;

CREATE INDEX IF NOT EXISTS idx_caregivers_role_active
ON caregivers(role, is_active, created_at);

CREATE INDEX IF NOT EXISTS idx_caregiver_patient_access_patient
ON caregiver_patient_access(patient_id, caregiver_id);

CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    mode TEXT NOT NULL,
    keyword_tags TEXT,
    repeated_flag INTEGER NOT NULL DEFAULT 0,
    quality_score REAL,
    quality_label TEXT,
    quality_note TEXT,
    FOREIGN KEY(user_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_updated_at
ON user_profiles(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_logs_user_time
ON chat_logs(user_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT DEFAULT (datetime('now')),
    quality_score REAL,
    quality_label TEXT,
    quality_note TEXT,
    quality_flags TEXT
);

CREATE INDEX IF NOT EXISTS idx_conversations_patient_time
ON conversations(patient_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_patient_session
ON conversations(patient_id, session_id, timestamp ASC);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_profile_id INTEGER NOT NULL,
    reminder_type TEXT NOT NULL,
    title TEXT NOT NULL,
    scheduled_time TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    confirmed_by TEXT NOT NULL DEFAULT 'unknown',
    confirmed_at TEXT,
    repeat_rule TEXT,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    created_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(user_profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_profile_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'low',
    description TEXT,
    source TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS caregiver_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_profile_id INTEGER NOT NULL,
    caregiver_name TEXT NOT NULL,
    caregiver_role TEXT,
    contact_info TEXT,
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reminders_profile_enabled
ON reminders(user_profile_id, is_enabled, scheduled_time);

CREATE TABLE IF NOT EXISTS medication_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    medication_name TEXT NOT NULL,
    remind_time TEXT NOT NULL,
    dose TEXT,
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_medication_schedule_patient_time
ON medication_schedule(patient_id, enabled, remind_time);

CREATE INDEX IF NOT EXISTS idx_event_logs_profile_time
ON event_logs(user_profile_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_caregiver_links_profile
ON caregiver_links(user_profile_id, is_primary DESC, id DESC);

CREATE TABLE IF NOT EXISTS caregiver_events (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    user_profile_id INTEGER,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'low',
    title TEXT,
    description TEXT,
    source_message TEXT,
    source_turn TEXT,
    assistant_reply TEXT,
    suggested_action TEXT,
    tags TEXT,
    created_at TEXT NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(user_profile_id) REFERENCES user_profiles(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_caregiver_events_patient_time
ON caregiver_events(patient_id, resolved, created_at DESC);

CREATE TABLE IF NOT EXISTS risk_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    risk_type TEXT,
    evidence TEXT,
    suggestion TEXT,
    is_resolved INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_risk_events_patient_time
ON risk_events(patient_id, is_resolved, created_at DESC);

CREATE TABLE IF NOT EXISTS patient_locations (
    patient_id TEXT PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    accuracy REAL,
    address_text TEXT,
    source TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS safe_zones (
    patient_id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    center_latitude REAL NOT NULL,
    center_longitude REAL NOT NULL,
    radius_meters REAL NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS location_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    distance_meters REAL NOT NULL,
    created_at TEXT NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_location_alerts_patient_time
ON location_alerts(patient_id, created_at DESC);

CREATE TABLE IF NOT EXISTS familiar_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    material_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    related_person TEXT,
    file_path TEXT,
    thumbnail_url TEXT,
    transcript_text TEXT,
    artist TEXT,
    use_scene TEXT,
    suggested_use_scene TEXT,
    related_time TEXT,
    sensitivity_level TEXT,
    tags TEXT,
    safety_note TEXT,
    is_sensitive INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(patient_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_familiar_materials_patient_type
ON familiar_materials(patient_id, material_type, updated_at DESC);

CREATE TABLE IF NOT EXISTS memory_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    source_message TEXT NOT NULL,
    suggested_title TEXT NOT NULL,
    suggested_description TEXT,
    suggested_material_type TEXT NOT NULL,
    related_person TEXT,
    sensitivity_level TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    dedup_warning TEXT,
    conflict_warning TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    FOREIGN KEY(patient_id) REFERENCES user_profiles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memory_candidates_patient_status
ON memory_candidates(patient_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS daily_care_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    date TEXT NOT NULL,
    medication_taken INTEGER,
    medication_time TEXT,
    risk_events INTEGER DEFAULT 0,
    conversation_count INTEGER DEFAULT 0,
    mood_score REAL,
    mood_label TEXT,
    mood_evidence TEXT,
    summary_text TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(patient_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_care_summary_patient_date
ON daily_care_summary(patient_id, date DESC);

CREATE TABLE IF NOT EXISTS consent_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    consented_by TEXT NOT NULL,
    consent_time TEXT NOT NULL,
    consent_version TEXT DEFAULT 'v1.0',
    ip_address TEXT,
    UNIQUE(patient_id, consent_version)
);

CREATE INDEX IF NOT EXISTS idx_consent_records_patient_version
ON consent_records(patient_id, consent_version);
"""

USER_PROFILE_REQUIRED_COLUMNS = {
    "family_info": "TEXT",
    "life_events": "TEXT",
    "preferences": "TEXT",
    "notes": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT",
}

CHAT_LOG_REQUIRED_COLUMNS = {
    "quality_score": "REAL",
    "quality_label": "TEXT",
    "quality_note": "TEXT",
}

CAREGIVER_EVENT_REQUIRED_COLUMNS = {
    "title": "TEXT",
    "description": "TEXT",
    "source_turn": "TEXT",
    "tags": "TEXT",
}

FAMILIAR_MATERIAL_REQUIRED_COLUMNS = {
    "related_person": "TEXT",
    "file_path": "TEXT",
    "thumbnail_url": "TEXT",
    "transcript_text": "TEXT",
    "artist": "TEXT",
    "use_scene": "TEXT",
    "suggested_use_scene": "TEXT",
    "related_time": "TEXT",
    "sensitivity_level": "TEXT",
    "tags": "TEXT",
    "safety_note": "TEXT",
    "photo_year": "INTEGER",
    "photo_decade": "TEXT",
    "story_text": "TEXT",
    "voice_note_path": "TEXT",
    "is_sensitive": "INTEGER NOT NULL DEFAULT 0",
    "is_active": "INTEGER NOT NULL DEFAULT 1",
    "updated_at": "TEXT",
}

REMINDER_REQUIRED_COLUMNS = {
    "description": "TEXT",
    "status": "TEXT NOT NULL DEFAULT 'pending'",
    "confirmed_by": "TEXT NOT NULL DEFAULT 'unknown'",
    "confirmed_at": "TEXT",
}

MEMORY_CANDIDATE_REQUIRED_COLUMNS = {
    "source_message": "TEXT",
    "suggested_title": "TEXT",
    "suggested_description": "TEXT",
    "suggested_material_type": "TEXT",
    "related_person": "TEXT",
    "sensitivity_level": "TEXT",
    "status": "TEXT NOT NULL DEFAULT 'pending'",
    "dedup_warning": "TEXT",
    "conflict_warning": "TEXT",
    "reviewed_at": "TEXT",
}

DAILY_CARE_SUMMARY_REQUIRED_COLUMNS = {
    "mood_label": "TEXT",
    "mood_evidence": "TEXT",
}


def _now_text() -> str:
    """Return a compact timestamp for migration backfills."""
    return datetime.now().isoformat(timespec="seconds")


def migrate_user_profiles_schema() -> None:
    """Backfill new columns for existing SQLite databases created by older versions."""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(user_profiles)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}

        for column_name, column_type in USER_PROFILE_REQUIRED_COLUMNS.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                f"ALTER TABLE user_profiles ADD COLUMN {column_name} {column_type}"
            )

        now = _now_text()
        if "created_at" not in existing_columns:
            connection.execute(
                "UPDATE user_profiles SET created_at = COALESCE(created_at, ?)",
                (now,),
            )
        if "updated_at" not in existing_columns:
            connection.execute(
                "UPDATE user_profiles SET updated_at = COALESCE(updated_at, created_at, ?)",
                (now,),
            )

        connection.commit()


def migrate_chat_logs_schema() -> None:
    """Backfill quality scoring columns for existing chat log tables."""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(chat_logs)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}

        for column_name, column_type in CHAT_LOG_REQUIRED_COLUMNS.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                f"ALTER TABLE chat_logs ADD COLUMN {column_name} {column_type}"
            )

        connection.commit()


def migrate_caregiver_events_schema() -> None:
    """Backfill readable caregiver event columns for existing databases."""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(caregiver_events)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}

        for column_name, column_type in CAREGIVER_EVENT_REQUIRED_COLUMNS.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                f"ALTER TABLE caregiver_events ADD COLUMN {column_name} {column_type}"
            )

        connection.commit()


def migrate_familiar_materials_schema() -> None:
    """Backfill columns for familiar materials created by earlier prototypes."""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(familiar_materials)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}

        for column_name, column_type in FAMILIAR_MATERIAL_REQUIRED_COLUMNS.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                f"ALTER TABLE familiar_materials ADD COLUMN {column_name} {column_type}"
            )

        now = _now_text()
        if existing_columns and "updated_at" not in existing_columns:
            connection.execute(
                "UPDATE familiar_materials SET updated_at = COALESCE(updated_at, created_at, ?)",
                (now,),
            )

        connection.commit()


def migrate_reminders_schema() -> None:
    """Backfill reminder status columns for older databases."""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(reminders)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}

        for column_name, column_type in REMINDER_REQUIRED_COLUMNS.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                f"ALTER TABLE reminders ADD COLUMN {column_name} {column_type}"
            )

        connection.execute(
            "UPDATE reminders SET status = COALESCE(status, 'pending') WHERE status IS NULL OR TRIM(status) = ''"
        )
        connection.execute(
            "UPDATE reminders SET confirmed_by = COALESCE(confirmed_by, 'unknown') WHERE confirmed_by IS NULL OR TRIM(confirmed_by) = ''"
        )
        connection.commit()


def migrate_memory_candidates_schema() -> None:
    """Backfill columns for caregiver-reviewed memory candidates."""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(memory_candidates)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}

        for column_name, column_type in MEMORY_CANDIDATE_REQUIRED_COLUMNS.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                f"ALTER TABLE memory_candidates ADD COLUMN {column_name} {column_type}"
            )

        if existing_columns:
            connection.execute(
                "UPDATE memory_candidates SET status = COALESCE(status, 'pending') WHERE status IS NULL OR TRIM(status) = ''"
            )
        connection.commit()


def migrate_daily_care_summary_schema() -> None:
    """Backfill columns for persisted cross-day care summaries."""
    with closing(get_connection()) as connection:
        existing_rows = connection.execute("PRAGMA table_info(daily_care_summary)").fetchall()
        existing_columns = {row["name"] for row in existing_rows}

        for column_name, column_type in DAILY_CARE_SUMMARY_REQUIRED_COLUMNS.items():
            if column_name in existing_columns:
                continue
            connection.execute(
                f"ALTER TABLE daily_care_summary ADD COLUMN {column_name} {column_type}"
            )

        connection.commit()


def initialize_database() -> None:
    """Create SQLite tables and seed one starter profile for a smooth first run."""
    with closing(get_connection()) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.commit()

    migrate_user_profiles_schema()
    migrate_chat_logs_schema()
    migrate_caregiver_events_schema()
    migrate_familiar_materials_schema()
    migrate_reminders_schema()
    migrate_memory_candidates_schema()
    migrate_daily_care_summary_schema()
    profile = ensure_default_profile()
    if profile.id is not None and profile.name in {"李奶奶", "李桂兰"}:
        familiar_material_service.seed_demo_materials(profile.id)


if __name__ == "__main__":
    initialize_database()
    print(f"Database ready at {DB_PATH}")
