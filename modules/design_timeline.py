"""Design Timeline: Visual project revision history and state rollback."""
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional
from config.settings import DB_PATH
from models.schemas import PaletteConcept
from modules.storage import get_db_connection, init_db


def save_timeline_version(
    user_id: str,
    project_id: str,
    palette: PaletteConcept,
    label: str,
    notes: str = "",
    thumbnail_data: str = "",
    db_path: str = DB_PATH
) -> str:
    """Save an immutable timeline snapshot version of a design session."""
    init_db(db_path)
    version_id = f"ver_{uuid.uuid4().hex[:10]}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Find next version number for this project
        cursor.execute(
            "SELECT COALESCE(MAX(version_num), 0) FROM design_timeline WHERE user_id = ? AND project_id = ?",
            (user_id, project_id)
        )
        row = cursor.fetchone()
        next_ver = (row[0] if row else 0) + 1
        
        cursor.execute(
            """
            INSERT INTO design_timeline (
                id, user_id, project_id, version_num, label, timestamp, palette_json, notes, thumbnail_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                user_id,
                project_id,
                next_ver,
                label.strip() or f"Iteration {next_ver}",
                now_str,
                json.dumps(palette.model_dump()),
                notes.strip(),
                thumbnail_data
            )
        )
        conn.commit()
    
    return version_id


def list_project_timeline(user_id: str, project_id: Optional[str] = None, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List timeline versions for a project or all projects of user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if project_id:
            cursor.execute(
                """
                SELECT * FROM design_timeline
                WHERE user_id = ? AND project_id = ?
                ORDER BY version_num DESC
                """,
                (user_id, project_id)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM design_timeline
                WHERE user_id = ?
                ORDER BY timestamp DESC
                """,
                (user_id,)
            )
        rows = cursor.fetchall()
        
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "user_id": r["user_id"],
            "project_id": r["project_id"],
            "version_num": r["version_num"],
            "label": r["label"],
            "timestamp": r["timestamp"],
            "palette": json.loads(r["palette_json"]),
            "notes": r["notes"] or "",
            "thumbnail_data": r["thumbnail_data"] or ""
        })
    return results


def get_timeline_version(version_id: str, user_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch specific version, ensuring user ownership."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM design_timeline WHERE id = ? AND user_id = ?",
            (version_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "project_id": row["project_id"],
            "version_num": row["version_num"],
            "label": row["label"],
            "timestamp": row["timestamp"],
            "palette": json.loads(row["palette_json"]),
            "notes": row["notes"] or "",
            "thumbnail_data": row["thumbnail_data"] or ""
        }
