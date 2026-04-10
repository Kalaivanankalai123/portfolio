from __future__ import annotations

import os
import sqlite3
import smtplib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

def resolve_db_path() -> Path:
    configured = os.getenv("VIEWER_DB_PATH", "").strip()
    if configured:
        return Path(configured)

    # Railway exposes this when a volume is attached.
    railway_mount = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
    if railway_mount:
        return Path(railway_mount) / "viewer_analytics.db"

    return BASE_DIR / "viewer_analytics.db"


DB_PATH = resolve_db_path()
SCHEMA_PATH = BASE_DIR / "data.sql"
PORTFOLIO_FILE = BASE_DIR / "portfolio.html"
ASSETS_DIR = BASE_DIR / "assets"
CONTACT_TO_EMAIL = os.getenv("CONTACT_TO_EMAIL", "kalaivanankkalai5@gmail.com")

def init_db() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

app = FastAPI(title="Viewer Analytics API", lifespan=lifespan)

# CORS Middleware to allow your frontend to talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your domain once deployed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if ASSETS_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

class ViewerIn(BaseModel):
    page: str = Field(default="/portfolio", max_length=255)
    referrer: str = Field(default="", max_length=500)
    user_agent: str = Field(default="", max_length=1000)
    language: str = Field(default="", max_length=50)
    platform: str = Field(default="", max_length=100)
    timezone: str = Field(default="", max_length=100)
    screen_width: int | None = Field(default=None, ge=0, le=10000)
    screen_height: int | None = Field(default=None, ge=0, le=10000)

class ContactMessageIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    phone: str = Field(min_length=5, max_length=50) # Added phone field
    message: str = Field(min_length=3, max_length=5000)

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _resolve_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return ""

def _send_contact_email(name: str, email: str, phone: str, message: str, submitted_at: str, ip_address: str) -> tuple[bool, str]:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    if not smtp_host:
        return False, "SMTP_HOST not configured"

    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes", "on")
    from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user or CONTACT_TO_EMAIL)

    msg = EmailMessage()
    msg["Subject"] = f"New portfolio contact from {name}"
    msg["From"] = from_email
    msg["To"] = CONTACT_TO_EMAIL
    msg["Reply-To"] = email
    
    msg.set_content(
        "You received a new portfolio message.\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n"
        f"Submitted (UTC): {submitted_at}\n"
        f"IP Address: {ip_address or 'unknown'}\n\n"
        "Message:\n"
        f"{message}\n"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            if use_tls:
                server.starttls()
            if smtp_user:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True, ""
    except Exception as exc:
        return False, str(exc)

@app.get("/")
def home() -> Response:
    if PORTFOLIO_FILE.is_file():
        return FileResponse(str(PORTFOLIO_FILE), media_type="text/html")
    return Response(content="portfolio.html not found", status_code=404)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "Viewer analytics backend is running"}

@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)

@app.get("/portfolio")
def portfolio() -> Response:
    if PORTFOLIO_FILE.is_file():
        return FileResponse(str(PORTFOLIO_FILE), media_type="text/html")
    return Response(content="portfolio.html not found", status_code=404)

@app.post("/api/viewers")
def create_viewer(payload: ViewerIn, request: Request) -> dict[str, Any]:
    visited_at = datetime.now(timezone.utc).isoformat()
    ip_address = _resolve_ip(request)
    user_agent = payload.user_agent or request.headers.get("user-agent", "")

    with _get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO viewer_details (
                visited_at, page, ip_address, user_agent, referrer,
                language, platform, timezone, screen_width, screen_height
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visited_at,
                payload.page,
                ip_address,
                user_agent,
                payload.referrer,
                payload.language,
                payload.platform,
                payload.timezone,
                payload.screen_width,
                payload.screen_height,
            ),
        )
        conn.commit()

    return {"status": "ok", "id": cur.lastrowid, "visited_at": visited_at}

@app.post("/api/portfolio/view")
def create_portfolio_view(payload: ViewerIn, request: Request) -> dict[str, Any]:
    """Compatibility endpoint for existing portfolio tracking script."""
    return create_viewer(payload, request)

@app.get("/api/viewers")
def list_viewers(limit: int = Query(default=20, ge=1, le=200)) -> dict[str, Any]:
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                id, visited_at, page, ip_address, user_agent, referrer,
                language, platform, timezone, screen_width, screen_height
            FROM viewer_details
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return {"count": len(rows), "items": [dict(row) for row in rows]}

@app.get("/api/viewers/stats")
def viewer_stats() -> dict[str, Any]:
    with _get_connection() as conn:
        total_views = conn.execute("SELECT COUNT(*) AS n FROM viewer_details").fetchone()["n"]
        unique_visitors = conn.execute(
            "SELECT COUNT(DISTINCT ip_address) AS n FROM viewer_details WHERE ip_address IS NOT NULL AND ip_address != ''"
        ).fetchone()["n"]
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_views = conn.execute(
            "SELECT COUNT(*) AS n FROM viewer_details WHERE substr(visited_at, 1, 10) = ?",
            (today,),
        ).fetchone()["n"]
        latest = conn.execute(
            "SELECT visit_date, total_views, unique_visitors FROM viewer_daily_summary LIMIT 7"
        ).fetchall()

    return {
        "total_views": total_views,
        "unique_visitors": unique_visitors,
        "today_views": today_views,
        "last_7_days": [dict(row) for row in latest],
    }

@app.post("/api/contact")
def create_contact_message(payload: ContactMessageIn, request: Request) -> dict[str, Any]:
    submitted_at = datetime.now(timezone.utc).isoformat()
    ip_address = _resolve_ip(request)
    user_agent = request.headers.get("user-agent", "")

    with _get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO contact_messages (
                submitted_at, name, email, phone, message, ip_address, user_agent, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submitted_at,
                payload.name.strip(),
                payload.email.strip(),
                payload.phone.strip(),
                payload.message.strip(),
                ip_address,
                user_agent,
                "received",
            ),
        )
        conn.commit()
        message_id = cur.lastrowid

    sent, error = _send_contact_email(
        name=payload.name.strip(),
        email=payload.email.strip(),
        phone=payload.phone.strip(),
        message=payload.message.strip(),
        submitted_at=submitted_at,
        ip_address=ip_address,
    )

    status = "emailed" if sent else "stored_only"
    with _get_connection() as conn:
        conn.execute("UPDATE contact_messages SET status = ? WHERE id = ?", (status, message_id))
        conn.commit()

    response: dict[str, Any] = {
        "status": "ok",
        "id": message_id,
        "submitted_at": submitted_at,
        "email_sent": sent,
    }
    if not sent:
        response["email_error"] = error
    return response

@app.get("/api/contact")
def list_contact_messages(limit: int = Query(default=20, ge=1, le=200)) -> dict[str, Any]:
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, submitted_at, name, email, phone, message, ip_address, status
            FROM contact_messages
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {"count": len(rows), "items": [dict(row) for row in rows]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
