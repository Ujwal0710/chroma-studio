"""Chroma Memory: Transparent personalized design-preference engine."""
import json
from typing import Dict, Any, List, Tuple
from config.settings import DB_PATH
from models.schemas import PaletteConcept
from modules.storage import get_db_connection, init_db


def get_chroma_memory(user_id: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Retrieve user's structured preference memory."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chroma_memory WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return {
                "user_id": user_id,
                "favorite_colors": [],
                "rejected_colors": [],
                "preferred_styles": [],
                "preferred_atmospheres": [],
                "interactions_count": 0
            }
        
        return {
            "user_id": user_id,
            "favorite_colors": json.loads(row["favorite_colors_json"] or "[]"),
            "rejected_colors": json.loads(row["rejected_colors_json"] or "[]"),
            "preferred_styles": json.loads(row["preferred_styles_json"] or "[]"),
            "preferred_atmospheres": json.loads(row["preferred_atmospheres_json"] or "[]"),
            "interactions_count": row["interactions_count"] or 0
        }


def record_favorite_palette(user_id: str, palette: PaletteConcept, style: str = "", db_path: str = DB_PATH) -> None:
    """Record a user-favorited palette into memory."""
    init_db(db_path)
    mem = get_chroma_memory(user_id, db_path=db_path)
    
    fav_colors = mem["favorite_colors"]
    for c in palette.all_colors():
        c_name = c.name or c.hex
        if c_name not in fav_colors:
            fav_colors.append(c_name)
    # Keep up to 20 most recent
    fav_colors = fav_colors[-20:]
    
    fav_atmos = mem["preferred_atmospheres"]
    if palette.atmosphere and palette.atmosphere not in fav_atmos:
        fav_atmos.append(palette.atmosphere)
    fav_atmos = fav_atmos[-10:]
    
    fav_styles = mem["preferred_styles"]
    if style and style not in fav_styles:
        fav_styles.append(style)
    fav_styles = fav_styles[-10:]
    
    interactions = mem["interactions_count"] + 1
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chroma_memory (user_id, favorite_colors_json, rejected_colors_json, preferred_styles_json, preferred_atmospheres_json, interactions_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                favorite_colors_json = excluded.favorite_colors_json,
                preferred_styles_json = excluded.preferred_styles_json,
                preferred_atmospheres_json = excluded.preferred_atmospheres_json,
                interactions_count = excluded.interactions_count
            """,
            (
                user_id,
                json.dumps(fav_colors),
                json.dumps(mem["rejected_colors"]),
                json.dumps(fav_styles),
                json.dumps(fav_atmos),
                interactions
            )
        )
        conn.commit()


def record_rejected_palette(user_id: str, palette: PaletteConcept, db_path: str = DB_PATH) -> None:
    """Record a rejected palette tone into memory."""
    init_db(db_path)
    mem = get_chroma_memory(user_id, db_path=db_path)
    
    rej_colors = mem["rejected_colors"]
    for c in palette.all_colors():
        c_name = c.name or c.hex
        if c_name not in rej_colors:
            rej_colors.append(c_name)
    rej_colors = rej_colors[-20:]
    
    interactions = mem["interactions_count"] + 1
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chroma_memory (user_id, favorite_colors_json, rejected_colors_json, preferred_styles_json, preferred_atmospheres_json, interactions_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                rejected_colors_json = excluded.rejected_colors_json,
                interactions_count = excluded.interactions_count
            """,
            (
                user_id,
                json.dumps(mem["favorite_colors"]),
                json.dumps(rej_colors),
                json.dumps(mem["preferred_styles"]),
                json.dumps(mem["preferred_atmospheres"]),
                interactions
            )
        )
        conn.commit()


def clear_chroma_memory(user_id: str, db_path: str = DB_PATH) -> None:
    """Reset preference memory for user."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chroma_memory WHERE user_id = ?", (user_id,))
        conn.commit()


def evaluate_chroma_memory_influence(user_id: str, palette: PaletteConcept, db_path: str = DB_PATH) -> Tuple[float, List[str]]:
    """
    Compute a transparent heuristic adjustment (+/- points) based on Chroma Memory:
    - +3 pts for each color matching a known favorite.
    - -5 pts for each color matching a rejected color.
    - +2 pts for matching preferred atmosphere.
    Returns (delta_score, explanation_list).
    """
    mem = get_chroma_memory(user_id, db_path=db_path)
    if mem["interactions_count"] == 0:
        return 0.0, ["Chroma Memory: No past interactions recorded yet."]
    
    delta = 0.0
    notes = []
    
    fav_set = set(c.lower() for c in mem["favorite_colors"])
    rej_set = set(c.lower() for c in mem["rejected_colors"])
    
    for c in palette.all_colors():
        name_lower = (c.name or "").lower()
        if name_lower in fav_set:
            delta += 2.5
            notes.append(f"+2.5 match with favorite tone '{c.name}'")
        if name_lower in rej_set:
            delta -= 4.0
            notes.append(f"-4.0 overlap with previously dismissed tone '{c.name}'")
            
    if palette.atmosphere in mem["preferred_atmospheres"]:
        delta += 2.0
        notes.append(f"+2.0 atmosphere alignment with '{palette.atmosphere}'")
    
    # Cap total influence between -12 and +12 to preserve primary CV integrity
    delta = max(-12.0, min(12.0, delta))
    return delta, notes
