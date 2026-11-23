"""SQLite database persistence for palettes, user preferences, authentication, subscriptions, and timeline."""
import sqlite3
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from config.settings import DB_PATH
from models.schemas import PaletteConcept, PreferenceSettings


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

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TEXT NOT NULL,
                avatar_url TEXT DEFAULT ''
            )
        """)

        # User profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                avatar_url TEXT DEFAULT '',
                preferred_language TEXT DEFAULT 'English',
                theme TEXT DEFAULT 'light',
                default_room_type TEXT DEFAULT 'Living Room',
                default_interior_style TEXT DEFAULT 'Modern',
                preferred_temp TEXT DEFAULT 'Balanced / Neutral',
                liked_colors_json TEXT DEFAULT '[]',
                disliked_colors_json TEXT DEFAULT '[]',
                preferred_atmospheres_json TEXT DEFAULT '[]',
                default_vis_mode TEXT DEFAULT 'Side-by-Side Comparison',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # User subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                status TEXT NOT NULL,
                billing_cycle TEXT NOT NULL,
                current_period_start TEXT NOT NULL,
                current_period_end TEXT NOT NULL,
                razorpay_subscription_id TEXT,
                razorpay_payment_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Usage records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                month_key TEXT NOT NULL,
                analyses_used INTEGER DEFAULT 0,
                ai_previews_used INTEGER DEFAULT 0,
                exports_count INTEGER DEFAULT 0,
                UNIQUE(user_id, month_key),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

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
                preview_image_path TEXT,
                user_id TEXT DEFAULT 'default_user'
            )
        """)

        # Check and migrate user_id column into saved_palettes if created in legacy schema
        cursor.execute("PRAGMA table_info(saved_palettes)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE saved_palettes ADD COLUMN user_id TEXT DEFAULT 'default_user'")

        # User preferences preset table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_preferences (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                preferences_json TEXT NOT NULL,
                user_id TEXT DEFAULT 'default_user'
            )
        """)

        # Design timeline table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS design_timeline (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                version_num INTEGER NOT NULL,
                label TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                palette_json TEXT NOT NULL,
                notes TEXT DEFAULT '',
                thumbnail_data TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Chroma Memory profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chroma_memory (
                user_id TEXT PRIMARY KEY,
                favorite_colors_json TEXT DEFAULT '[]',
                rejected_colors_json TEXT DEFAULT '[]',
                preferred_styles_json TEXT DEFAULT '[]',
                preferred_atmospheres_json TEXT DEFAULT '[]',
                interactions_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Payment events table (for idempotency)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_events (
                event_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                verified INTEGER DEFAULT 1,
                timestamp TEXT NOT NULL
            )
        """)

        # Login attempts table (for rate-limiting)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                success INTEGER NOT NULL
            )
        """)

        # Password reset tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                email TEXT NOT NULL,
                token_hash TEXT PRIMARY KEY,
                expires_at TEXT NOT NULL
            )
        """)

        # Scanned colors table (Live Color Scanner)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanned_colors (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                hex TEXT NOT NULL,
                rgb_json TEXT NOT NULL,
                hsv_json TEXT NOT NULL,
                lab_json TEXT NOT NULL,
                temperature TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                notes TEXT DEFAULT '',
                source TEXT DEFAULT 'live_camera',
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Room plans table (Smart Furniture & Room Planner)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS room_plans (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                room_type TEXT NOT NULL,
                length_m REAL NOT NULL,
                width_m REAL NOT NULL,
                height_m REAL NOT NULL,
                furniture_json TEXT DEFAULT '[]',
                clearances_json TEXT DEFAULT '[]',
                notes TEXT DEFAULT '',
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Renovation shopping lists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_name TEXT NOT NULL,
                items_json TEXT NOT NULL,
                total_budget_inr REAL DEFAULT 0.0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Home maintenance logs & reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                room_name TEXT NOT NULL,
                photo_data TEXT DEFAULT '',
                damage_type TEXT DEFAULT 'None',
                severity TEXT DEFAULT 'Low',
                notes TEXT DEFAULT '',
                maintenance_activity TEXT DEFAULT '',
                reminder_date TEXT DEFAULT '',
                is_resolved INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Chroma AI Assistant messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assistant_messages (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                context_json TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Create indexes for fast querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_palettes_user ON saved_palettes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_user_proj ON design_timeline(user_id, project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage_records(user_id, month_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scanned_colors_user ON scanned_colors(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_room_plans_user ON room_plans(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopping_lists_user ON shopping_lists(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maintenance_records_user ON maintenance_records(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assistant_user_session ON assistant_messages(user_id, session_id)")

        conn.commit()


# ----------------------------------------------------
# User & Profile Storage
# ----------------------------------------------------
def create_user_record(email: str, password_hash: str, salt: str, full_name: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Create user and initialize profile and free subscription."""
    init_db(db_path)
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    now_str = datetime.datetime.now().isoformat()
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (id, email, password_hash, salt, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?, 'user', ?)
            """,
            (user_id, email, password_hash, salt, full_name, now_str)
        )
        
        # Default profile
        cursor.execute(
            """
            INSERT INTO user_profiles (
                user_id, display_name, avatar_url, preferred_language, theme,
                default_room_type, default_interior_style, preferred_temp,
                liked_colors_json, disliked_colors_json, preferred_atmospheres_json, default_vis_mode
            ) VALUES (?, ?, '', 'English', 'light', 'Living Room', 'Modern', 'Balanced / Neutral', '["Warm Linen", "Desert Sand"]', '[]', '["Calm & Relaxing"]', 'Side-by-Side Comparison')
            """,
            (user_id, full_name)
        )
        
        # Free subscription initial state
        month_end = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
        cursor.execute(
            """
            INSERT INTO user_subscriptions (
                user_id, plan_id, status, billing_cycle, current_period_start, current_period_end
            ) VALUES (?, 'free', 'active', 'monthly', ?, ?)
            """,
            (user_id, now_str, month_end)
        )
        
        # Initialize chroma memory
        cursor.execute(
            """
            INSERT INTO chroma_memory (user_id, favorite_colors_json, rejected_colors_json, preferred_styles_json, preferred_atmospheres_json, interactions_count)
            VALUES (?, '[]', '[]', '[]', '[]', 0)
            """,
            (user_id,)
        )
        
        conn.commit()
    
    return get_user_by_id(user_id, db_path=db_path)


def get_user_by_email(email: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by email."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by ID."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user_password(email: str, password_hash: str, salt: str, db_path: str = DB_PATH) -> bool:
    """Update password hash and salt for a user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE lower(email) = lower(?)",
            (password_hash, salt, email.strip())
        )
        conn.commit()
        return cursor.rowcount > 0


def get_user_profile(user_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve full profile for user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["liked_colors"] = json.loads(d.get("liked_colors_json") or "[]")
        d["disliked_colors"] = json.loads(d.get("disliked_colors_json") or "[]")
        d["preferred_atmospheres"] = json.loads(d.get("preferred_atmospheres_json") or "[]")
        return d


def update_user_profile(user_id: str, profile_data: Dict[str, Any], db_path: str = DB_PATH) -> bool:
    """Update profile settings for user."""
    init_db(db_path)
    liked_json = json.dumps(profile_data.get("liked_colors", []))
    disliked_json = json.dumps(profile_data.get("disliked_colors", []))
    atmos_json = json.dumps(profile_data.get("preferred_atmospheres", []))
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_profiles (
                user_id, display_name, avatar_url, preferred_language, theme,
                default_room_type, default_interior_style, preferred_temp,
                liked_colors_json, disliked_colors_json, preferred_atmospheres_json, default_vis_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                display_name = excluded.display_name,
                avatar_url = excluded.avatar_url,
                preferred_language = excluded.preferred_language,
                theme = excluded.theme,
                default_room_type = excluded.default_room_type,
                default_interior_style = excluded.default_interior_style,
                preferred_temp = excluded.preferred_temp,
                liked_colors_json = excluded.liked_colors_json,
                disliked_colors_json = excluded.disliked_colors_json,
                preferred_atmospheres_json = excluded.preferred_atmospheres_json,
                default_vis_mode = excluded.default_vis_mode
            """,
            (
                user_id,
                profile_data.get("display_name", "Designer"),
                profile_data.get("avatar_url", ""),
                profile_data.get("preferred_language", "English"),
                profile_data.get("theme", "light"),
                profile_data.get("default_room_type", "Living Room"),
                profile_data.get("default_interior_style", "Modern"),
                profile_data.get("preferred_temp", "Balanced / Neutral"),
                liked_json,
                disliked_json,
                atmos_json,
                profile_data.get("default_vis_mode", "Side-by-Side Comparison")
            )
        )
        conn.commit()
        return True


def delete_user_account_cascade(user_id: str, db_path: str = DB_PATH) -> bool:
    """Permanently delete user account and all personal design data."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM saved_palettes WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM design_timeline WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM chroma_memory WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM usage_records WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_subscriptions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True


def export_user_data_bundle(user_id: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Retrieve full personal design data archive for GDPR/account export."""
    init_db(db_path)
    user = get_user_by_id(user_id, db_path=db_path)
    profile = get_user_profile(user_id, db_path=db_path)
    palettes = list_saved_palettes(db_path=db_path, user_id=user_id)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM design_timeline WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        timeline = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM user_subscriptions WHERE user_id = ?", (user_id,))
        sub_row = cursor.fetchone()
        sub = dict(sub_row) if sub_row else {}
    
    return {
        "export_timestamp": datetime.datetime.now().isoformat(),
        "user_account": {
            "id": user.get("id") if user else user_id,
            "email": user.get("email") if user else "",
            "full_name": user.get("full_name") if user else "",
            "created_at": user.get("created_at") if user else ""
        },
        "profile": profile or {},
        "subscription": sub,
        "saved_palettes_count": len(palettes),
        "saved_palettes": palettes,
        "timeline_versions_count": len(timeline),
        "timeline_versions": timeline
    }


# ----------------------------------------------------
# Rate Limiting & Password Reset Tokens
# ----------------------------------------------------
def record_login_attempt(email: str, success: bool, db_path: str = DB_PATH) -> None:
    """Record an authentication attempt."""
    init_db(db_path)
    now_str = datetime.datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_attempts (email, timestamp, success) VALUES (?, ?, ?)",
            (email.strip().lower(), now_str, 1 if success else 0)
        )
        conn.commit()


def get_recent_failed_login_count(email: str, minutes: int = 15, db_path: str = DB_PATH) -> int:
    """Count failed logins in past N minutes."""
    init_db(db_path)
    cutoff = (datetime.datetime.now() - datetime.timedelta(minutes=minutes)).isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM login_attempts
            WHERE lower(email) = lower(?) AND success = 0 AND timestamp >= ?
            """,
            (email.strip(), cutoff)
        )
        row = cursor.fetchone()
        return row[0] if row else 0


def clear_login_attempts(email: str, db_path: str = DB_PATH) -> None:
    """Clear failed login attempts upon successful authentication."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM login_attempts WHERE lower(email) = lower(?)", (email.strip(),))
        conn.commit()


def store_password_reset_token(email: str, token_hash: str, expires_at: str, db_path: str = DB_PATH) -> None:
    """Store active password reset token hash."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM password_resets WHERE lower(email) = lower(?)", (email.strip(),))
        cursor.execute(
            "INSERT INTO password_resets (email, token_hash, expires_at) VALUES (?, ?, ?)",
            (email.strip().lower(), token_hash, expires_at)
        )
        conn.commit()


def verify_and_consume_reset_token(token_hash: str, db_path: str = DB_PATH) -> Optional[str]:
    """Verify reset token, consume it, and return associated email if valid."""
    init_db(db_path)
    now_str = datetime.datetime.now().isoformat()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT email, expires_at FROM password_resets WHERE token_hash = ?",
            (token_hash,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        email = row["email"]
        expires_at = row["expires_at"]
        if expires_at < now_str:
            cursor.execute("DELETE FROM password_resets WHERE token_hash = ?", (token_hash,))
            conn.commit()
            return None
        
        # Token is valid: consume it
        cursor.execute("DELETE FROM password_resets WHERE token_hash = ?", (token_hash,))
        conn.commit()
        return email


# ----------------------------------------------------
# Palettes Storage (Preserves original API + user_id)
# ----------------------------------------------------
def save_palette(
    palette: PaletteConcept,
    custom_name: str,
    room_type: str,
    interior_style: str,
    preferences: Optional[PreferenceSettings] = None,
    notes: str = "",
    preview_image_path: Optional[str] = None,
    db_path: str = DB_PATH,
    user_id: str = "default_user"
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
                palette_json, preferences_json, notes, preview_image_path, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                preview_image_path or "",
                user_id
            )
        )
        conn.commit()

    return record_id


def list_saved_palettes(db_path: str = DB_PATH, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve saved palettes ordered by timestamp descending. Optionally filter by user_id."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM saved_palettes WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        else:
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
            "preview_image_path": r["preview_image_path"] or "",
            "user_id": r["user_id"] if "user_id" in r.keys() else "default_user"
        })
    return results


def get_saved_palette_by_id(record_id: str, db_path: str = DB_PATH, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single saved palette record by its ID, enforcing user ownership if user_id specified."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM saved_palettes WHERE id = ? AND user_id = ?", (record_id, user_id))
        else:
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
        "preview_image_path": r["preview_image_path"] or "",
        "user_id": r["user_id"] if "user_id" in r.keys() else "default_user"
    }


def delete_saved_palette(record_id: str, db_path: str = DB_PATH, user_id: Optional[str] = None) -> bool:
    """Delete a saved palette by ID. If user_id provided, ensures user ownership."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("DELETE FROM saved_palettes WHERE id = ? AND user_id = ?", (record_id, user_id))
        else:
            cursor.execute("DELETE FROM saved_palettes WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0


def count_user_saved_palettes(user_id: str, db_path: str = DB_PATH) -> int:
    """Count how many palettes the user has saved."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM saved_palettes WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0


def save_user_preferences_preset(
    preset_name: str,
    preferences: PreferenceSettings,
    db_path: str = DB_PATH,
    user_id: str = "default_user"
) -> str:
    """Save user preferences preset to database."""
    init_db(db_path)
    preset_id = f"pref_{uuid.uuid4().hex[:8]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO saved_preferences (id, name, timestamp, preferences_json, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (preset_id, preset_name.strip() or "Default Preset", now_str, json.dumps(preferences.model_dump()), user_id)
        )
        conn.commit()

    return preset_id


def list_saved_preferences_presets(db_path: str = DB_PATH, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all saved user preference presets."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM saved_preferences WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        else:
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


# ----------------------------------------------------
# Scanned Colors Storage (Live Color Scanner)
# ----------------------------------------------------
def save_scanned_color(
    user_id: str,
    color_data: Dict[str, Any],
    db_path: str = DB_PATH
) -> str:
    """Save a live scanned color swatch into the user's personal Chroma library."""
    init_db(db_path)
    scan_id = f"col_{uuid.uuid4().hex[:10]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scanned_colors (
                id, user_id, name, hex, rgb_json, hsv_json, lab_json, temperature, timestamp, notes, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_id,
                user_id,
                color_data.get("name", "Custom Shade"),
                color_data.get("hex", "#000000").upper(),
                json.dumps(color_data.get("rgb", (0, 0, 0))),
                json.dumps(color_data.get("hsv", (0, 0, 0))),
                json.dumps(color_data.get("lab", (0, 0, 0))),
                color_data.get("temperature", "neutral"),
                now_str,
                color_data.get("notes", ""),
                color_data.get("source", "live_camera")
            )
        )
        conn.commit()
    return scan_id


def list_scanned_colors(user_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List scanned colors in reverse chronological order for a user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM scanned_colors WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        rows = cursor.fetchall()

    return [
        {
            "id": r["id"],
            "user_id": r["user_id"],
            "name": r["name"],
            "hex": r["hex"],
            "rgb": tuple(json.loads(r["rgb_json"])),
            "hsv": tuple(json.loads(r["hsv_json"])),
            "lab": tuple(json.loads(r["lab_json"])),
            "temperature": r["temperature"],
            "timestamp": r["timestamp"],
            "notes": r["notes"],
            "source": r["source"]
        }
        for r in rows
    ]


def delete_scanned_color(color_id: str, user_id: str, db_path: str = DB_PATH) -> bool:
    """Delete a scanned color, verifying user ownership."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM scanned_colors WHERE id = ? AND user_id = ?",
            (color_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ----------------------------------------------------
# Room Plans Storage (Smart Furniture & Room Planner)
# ----------------------------------------------------
def save_room_plan(
    user_id: str,
    plan_data: Dict[str, Any],
    db_path: str = DB_PATH
) -> str:
    """Save an architectural room layout and furniture placement plan."""
    init_db(db_path)
    plan_id = plan_data.get("id") or f"plan_{uuid.uuid4().hex[:10]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO room_plans (
                id, user_id, name, room_type, length_m, width_m, height_m,
                furniture_json, clearances_json, notes, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                room_type = excluded.room_type,
                length_m = excluded.length_m,
                width_m = excluded.width_m,
                height_m = excluded.height_m,
                furniture_json = excluded.furniture_json,
                clearances_json = excluded.clearances_json,
                notes = excluded.notes,
                timestamp = excluded.timestamp
            """,
            (
                plan_id,
                user_id,
                plan_data.get("name", "New Room Layout"),
                plan_data.get("room_type", "Living Room"),
                float(plan_data.get("length_m", 5.0)),
                float(plan_data.get("width_m", 4.0)),
                float(plan_data.get("height_m", 2.8)),
                json.dumps(plan_data.get("furniture", [])),
                json.dumps(plan_data.get("clearances", [])),
                plan_data.get("notes", ""),
                now_str
            )
        )
        conn.commit()
    return plan_id


def list_room_plans(user_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List all saved room layouts for a user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM room_plans WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        rows = cursor.fetchall()

    return [
        {
            "id": r["id"],
            "user_id": r["user_id"],
            "name": r["name"],
            "room_type": r["room_type"],
            "length_m": r["length_m"],
            "width_m": r["width_m"],
            "height_m": r["height_m"],
            "furniture": json.loads(r["furniture_json"] or "[]"),
            "clearances": json.loads(r["clearances_json"] or "[]"),
            "notes": r["notes"],
            "timestamp": r["timestamp"]
        }
        for r in rows
    ]


def delete_room_plan(plan_id: str, user_id: str, db_path: str = DB_PATH) -> bool:
    """Delete a room plan with user ownership validation."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM room_plans WHERE id = ? AND user_id = ?",
            (plan_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ----------------------------------------------------
# Renovation Shopping Lists Storage
# ----------------------------------------------------
def save_shopping_list(
    user_id: str,
    shopping_data: Dict[str, Any],
    db_path: str = DB_PATH
) -> str:
    """Save or update a project renovation shopping list."""
    init_db(db_path)
    list_id = shopping_data.get("id") or f"shop_{uuid.uuid4().hex[:10]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO shopping_lists (id, user_id, project_name, items_json, total_budget_inr, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                project_name = excluded.project_name,
                items_json = excluded.items_json,
                total_budget_inr = excluded.total_budget_inr,
                timestamp = excluded.timestamp
            """,
            (
                list_id,
                user_id,
                shopping_data.get("project_name", "Room Renovation"),
                json.dumps(shopping_data.get("items", [])),
                float(shopping_data.get("total_budget_inr", 0.0)),
                now_str
            )
        )
        conn.commit()
    return list_id


def list_shopping_lists(user_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List all renovation shopping lists for user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM shopping_lists WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        rows = cursor.fetchall()

    return [
        {
            "id": r["id"],
            "user_id": r["user_id"],
            "project_name": r["project_name"],
            "items": json.loads(r["items_json"] or "[]"),
            "total_budget_inr": r["total_budget_inr"],
            "timestamp": r["timestamp"]
        }
        for r in rows
    ]


def delete_shopping_list(list_id: str, user_id: str, db_path: str = DB_PATH) -> bool:
    """Delete a renovation shopping list with user verification."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM shopping_lists WHERE id = ? AND user_id = ?",
            (list_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ----------------------------------------------------
# Home Maintenance Storage & Reminders
# ----------------------------------------------------
def save_maintenance_record(
    user_id: str,
    record_data: Dict[str, Any],
    db_path: str = DB_PATH
) -> str:
    """Save an inspection photograph, damage note, or maintenance activity."""
    init_db(db_path)
    rec_id = record_data.get("id") or f"maint_{uuid.uuid4().hex[:10]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maintenance_records (
                id, user_id, room_name, photo_data, damage_type, severity,
                notes, maintenance_activity, reminder_date, is_resolved, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                room_name = excluded.room_name,
                photo_data = excluded.photo_data,
                damage_type = excluded.damage_type,
                severity = excluded.severity,
                notes = excluded.notes,
                maintenance_activity = excluded.maintenance_activity,
                reminder_date = excluded.reminder_date,
                is_resolved = excluded.is_resolved,
                timestamp = excluded.timestamp
            """,
            (
                rec_id,
                user_id,
                record_data.get("room_name", "Living Room"),
                record_data.get("photo_data", ""),
                record_data.get("damage_type", "None"),
                record_data.get("severity", "Low"),
                record_data.get("notes", ""),
                record_data.get("maintenance_activity", ""),
                record_data.get("reminder_date", ""),
                1 if record_data.get("is_resolved") else 0,
                now_str
            )
        )
        conn.commit()
    return rec_id


def list_maintenance_records(user_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List all maintenance logs for a user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM maintenance_records WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        rows = cursor.fetchall()

    return [
        {
            "id": r["id"],
            "user_id": r["user_id"],
            "room_name": r["room_name"],
            "photo_data": r["photo_data"],
            "damage_type": r["damage_type"],
            "severity": r["severity"],
            "notes": r["notes"],
            "maintenance_activity": r["maintenance_activity"],
            "reminder_date": r["reminder_date"],
            "is_resolved": bool(r["is_resolved"]),
            "timestamp": r["timestamp"]
        }
        for r in rows
    ]


def delete_maintenance_record(rec_id: str, user_id: str, db_path: str = DB_PATH) -> bool:
    """Delete a maintenance log entry."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM maintenance_records WHERE id = ? AND user_id = ?",
            (rec_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ----------------------------------------------------
# Chroma AI Assistant Conversation Storage
# ----------------------------------------------------
def save_assistant_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    context_data: Optional[Dict[str, Any]] = None,
    db_path: str = DB_PATH
) -> str:
    """Persist an assistant or user conversation message with contextual metadata."""
    init_db(db_path)
    msg_id = f"msg_{uuid.uuid4().hex[:10]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assistant_messages (id, user_id, session_id, role, content, context_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg_id,
                user_id,
                session_id,
                role,
                content,
                json.dumps(context_data or {}),
                now_str
            )
        )
        conn.commit()
    return msg_id


def get_assistant_history(
    user_id: str,
    session_id: str,
    limit: int = 50,
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """Retrieve chronologically ordered message history for a user chat session."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM assistant_messages
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
            """,
            (user_id, session_id, limit)
        )
        rows = cursor.fetchall()

    return [
        {
            "id": r["id"],
            "role": r["role"],
            "content": r["content"],
            "context": json.loads(r["context_json"] or "{}"),
            "timestamp": r["timestamp"]
        }
        for r in rows
    ]


def clear_assistant_history(
    user_id: str,
    session_id: str,
    db_path: str = DB_PATH
) -> None:
    """Clear conversation history for a given session."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM assistant_messages WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        conn.commit()
