# app/routers/dashboard.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone

from ..deps import get_db
from .. import models

router = APIRouter(tags=["dashboard"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)
    since_365d = now - timedelta(days=365)

    total_events = db.query(func.count(models.BrowserEvent.id)).scalar() or 0
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_sessions = db.query(func.count(models.Session.id)).scalar() or 0

    events_last_24h = (
        db.query(func.count(models.BrowserEvent.id))
        .filter(models.BrowserEvent.timestamp >= since_24h)
        .scalar()
        or 0
    )

    # Top 5 Nutzer
    top_users = (
        db.query(
            models.User.display_name,
            models.User.external_id,
            func.count(models.BrowserEvent.id).label("event_count"),
        )
        .join(models.Session, models.User.id == models.Session.user_id)
        .join(models.BrowserEvent, models.Session.id == models.BrowserEvent.session_id)
        .group_by(models.User.id)
        .order_by(desc("event_count"))
        .limit(5)
        .all()
    )

    # Top 5 Seiten
    top_pages = (
        db.query(
            models.BrowserEvent.page_url,
            func.count(models.BrowserEvent.id).label("event_count"),
        )
        .group_by(models.BrowserEvent.page_url)
        .order_by(desc("event_count"))
        .limit(5)
        .all()
    )

    # Events pro Tag (letzte 365 Tage)
    events_by_day = (
        db.query(
            func.date(models.BrowserEvent.timestamp).label("day"),
            func.count(models.BrowserEvent.id).label("count"),
        )
        .filter(models.BrowserEvent.timestamp >= since_365d)
        .group_by("day")
        .order_by("day")
        .all()
    )

    # Events pro Stunde (heute, 0–23 Uhr)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    events_by_hour_today = (
        db.query(
            func.strftime("%H", models.BrowserEvent.timestamp).label("hour"),
            func.count(models.BrowserEvent.id).label("count"),
        )
        .filter(
            models.BrowserEvent.timestamp >= today_start,
            models.BrowserEvent.timestamp < tomorrow_start,
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_events": total_events,
            "total_users": total_users,
            "total_sessions": total_sessions,
            "events_last_24h": events_last_24h,
            "top_users": top_users,
            "top_pages": top_pages,
            "events_by_day": events_by_day,
            "events_by_hour_today": events_by_hour_today,
        },
    )
