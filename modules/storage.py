"""SQLite database persistence for palettes, user preferences, and historical records."""
import sqlite3
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import DB_PATH
from contextlib import contextmanager


@contextmanager
def get_db_connection(db_path: str = DB_PATH):
    """Create and yield SQLite database connection with row factory, closing on exit."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize database tables with migration-safe schema (IF NOT EXISTS)."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Palettes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_palettes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                room_type TEXT NOT NULL,
                interior_style TEXT NOT NULL,
                palette_json TEXT NOT NULL,
                preferences_json TEXT NOT NULL,
                notes TEXT,
                preview_image_path TEXT
            )
        """)

        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_preferences (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                preferences_json TEXT NOT NULL
            )
        """)

        conn.commit()


def save_palette(
    palette: PaletteConcept,
    custom_name: str,
    room_type: str,
    interior_style: str,
    preferences: Optional[PreferenceSettings] = None,
    notes: str = "",
    preview_image_path: Optional[str] = None,
    db_path: str = DB_PATH
) -> str:
    """Save a palette and its metadata to SQLite. Returns record ID."""
    init_db(db_path)
    record_id = f"pal_{uuid.uuid4().hex[:12]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    palette_dict = palette.model_dump()
    prefs_dict = preferences.model_dump() if preferences else {}

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO saved_palettes (
                id, name, timestamp, room_type, interior_style,
                palette_json, preferences_json, notes, preview_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                custom_name.strip() or palette.name,
                now_str,
                room_type,
                interior_style,
                json.dumps(palette_dict),
                json.dumps(prefs_dict),
                notes.strip(),
                preview_image_path or ""
            )
        )
        conn.commit()

    return record_id


def list_saved_palettes(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all saved palettes ordered by timestamp descending."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM saved_palettes ORDER BY timestamp DESC")
        rows = cursor.fetchall()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "timestamp": r["timestamp"],
            "room_type": r["room_type"],
            "interior_style": r["interior_style"],
            "palette": json.loads(r["palette_json"]),
            "preferences": json.loads(r["preferences_json"]),
            "notes": r["notes"] or "",
            "preview_image_path": r["preview_image_path"] or ""
        })
    return results


def get_saved_palette_by_id(record_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single saved palette record by its ID."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM saved_palettes WHERE id = ?", (record_id,))
        r = cursor.fetchone()

    if not r:
        return None

    return {
        "id": r["id"],
        "name": r["name"],
        "timestamp": r["timestamp"],
        "room_type": r["room_type"],
        "interior_style": r["interior_style"],
        "palette": json.loads(r["palette_json"]),
        "preferences": json.loads(r["preferences_json"]),
        "notes": r["notes"] or "",
        "preview_image_path": r["preview_image_path"] or ""
    }


def delete_saved_palette(record_id: str, db_path: str = DB_PATH) -> bool:
    """Delete a saved palette by ID. Returns True if deleted."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM saved_palettes WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0


def save_user_preferences_preset(
    preset_name: str,
    preferences: PreferenceSettings,
    db_path: str = DB_PATH
) -> str:
    """Save user preferences preset to database."""
    init_db(db_path)
    preset_id = f"pref_{uuid.uuid4().hex[:8]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO saved_preferences (id, name, timestamp, preferences_json)
            VALUES (?, ?, ?, ?)
            """,
            (preset_id, preset_name.strip() or "Default Preset", now_str, json.dumps(preferences.model_dump()))
        )
        conn.commit()

    return preset_id


def list_saved_preferences_presets(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List all saved user preference presets."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM saved_preferences ORDER BY timestamp DESC")
        rows = cursor.fetchall()

    return [
        {
            "id": r["id"],
            "name": r["name"],
            "timestamp": r["timestamp"],
            "preferences": json.loads(r["preferences_json"])
        }
        for r in rows
    ]
