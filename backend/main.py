"""FastAPI application entrypoint for CHROMA STUDIO AI Backend."""
import os
import base64
import logging
import traceback
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config.settings import APP_NAME, APP_TAGLINE, VISION_API_KEY
from modules.storage import init_db

# Import routers
from backend.routers import (
    auth,
    rooms,
    palettes,
    lighting_materials,
    estimator,
    timeline,
    memory_dna,
    billing,
    exports,
    account,
    room_3d
)

logger = logging.getLogger("chroma_studio")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Initialize database schema
init_db()

app = FastAPI(
    title=f"{APP_NAME} — API",
    description=f"{APP_TAGLINE}. Production REST backend wrapping architectural computer vision, colour science, and 3D simulation.",
    version="3.0.0"
)

# CORS Configuration for frontend (local dev + Render production)
# Explicit origins required because allow_credentials=True forbids wildcard "*".
raw_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://chroma-studio-theta.vercel.app"
)
ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization", "X-Requested-With"],
)


# ---------------------------------------------------------------------------
# Global exception handlers – every response gets JSON + CORS headers intact
# ---------------------------------------------------------------------------

def _cors_headers(request: Request) -> dict[str, str]:
    """Return CORS headers matching the incoming origin, or empty dict."""
    origin = request.headers.get("origin", "")
    if origin and (origin in ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "detail": exc.detail
        },
        headers=_cors_headers(request),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(x) for x in err.get("loc", [])])
        errors.append(f"{loc}: {err.get('msg')}")
    detail_msg = f"Validation error in request parameters: {'; '.join(errors)}" if errors else "Validation error in request parameters."
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": 422,
            "detail": detail_msg,
            "errors": errors
        },
        headers=_cors_headers(request),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the full traceback so it appears in the backend console/logs.
    logger.error(
        "Unhandled exception on %s %s:\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": 500,
            "detail": f"Internal server error: {type(exc).__name__}: {exc}"
        },
        headers=_cors_headers(request),
    )


# Include all modular routers
app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(palettes.router)
app.include_router(lighting_materials.router)
app.include_router(estimator.router)
app.include_router(timeline.router)
app.include_router(memory_dna.router)
app.include_router(billing.router)
app.include_router(exports.router)
app.include_router(account.router)
app.include_router(room_3d.router)


@app.get("/health")
def health_check():
    """Health check endpoint indicating service availability and offline AI status."""
    is_offline = not bool(VISION_API_KEY and VISION_API_KEY.strip())
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": "3.0.0",
        "offline_mode": is_offline,
        "vision_provider": "Local Computer Vision" if is_offline else "Cloud Vision LLM"
    }


@app.get("/rooms/sample")
def get_sample_room():
    """Provide verified physical architectural sample room for client demonstrations."""
    sample_path = Path(__file__).resolve().parent.parent / "data" / "roomie_default_room.jpg"
    if not sample_path.exists():
        return JSONResponse(status_code=404, content={"status": "error", "detail": "Sample room image file not found."})

    with open(sample_path, "rb") as f:
        raw_bytes = f.read()

    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    return {
        "status": "success",
        "filename": "roomie_default_room.jpg",
        "content_type": "image/jpeg",
        "image_data_url": f"data:image/jpeg;base64,{b64}",
        "image_data": f"data:image/jpeg;base64,{b64}"
    }
