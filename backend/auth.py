"""JWT Authentication and session cookie management for FastAPI."""
import datetime
from typing import Optional, Dict, Any
import jwt
from fastapi import Request, HTTPException, status, Depends
from config.settings import DB_PATH, AUTH_SECRET_KEY
from modules.storage import get_user_by_id

JWT_SECRET = AUTH_SECRET_KEY if AUTH_SECRET_KEY else "chroma_studio_jwt_secret_dev_key_2026"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72


def create_access_token(user_id: str, email: str, role: str = "designer") -> str:
    """Create signed JWT access token with expiration."""
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": exp,
        "iat": datetime.datetime.now(datetime.timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate signed JWT access token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Extract authenticated user from httpOnly cookie or Authorization header. Returns None if unauthenticated."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = get_user_by_id(user_id, db_path=DB_PATH)
    return user


def require_authenticated_user(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)) -> Dict[str, Any]:
    """Dependency ensuring user is signed in, raising 401 otherwise."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access this resource."
        )
    return current_user
