# app/routers/dashboard_users.py

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..deps import get_db
from .. import models

router = APIRouter(prefix="/users", tags=["users"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/", name="users_overview")
async def users_overview(request: Request, db: Session = Depends(get_db)):
    """
    Übersicht aller bekannten Nutzer mit Event-Anzahl und letzter Aktivität.
    """

    user_stats = (
        db.query(
            models.User.id,
            models.User.external_id,
            models.User.display_name,
            func.count(models.BrowserEvent.id).label("event_count"),
            func.max(models.BrowserEvent.timestamp).label("last_activity"),
        )
        .outerjoin(models.BrowserEvent, models.BrowserEvent.user_id == models.User.id)
        .group_by(models.User.id)
        .order_by(desc("event_count"))
        .all()
    )

    return templates.TemplateResponse(
        "users_overview.html",
        {
            "request": request,
            "users": user_stats,
        },
    )


@router.get("/{user_id}", name="users_user_detail")
async def users_user_detail(
    user_id: int, request: Request, db: Session = Depends(get_db)
):
    """
    Detailansicht für einen Nutzer:
    - Basis-KPIs
    - Top Business Central Seiten
    - Verteilung nach Aktionstyp
    - Letzte Events (Timeline)
    """

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Basisstats für KPIs
    stats = (
        db.query(
            func.count(models.BrowserEvent.id).label("event_count"),
            func.min(models.BrowserEvent.timestamp).label("first_activity"),
            func.max(models.BrowserEvent.timestamp).label("last_activity"),
            func.count(func.distinct(models.BrowserEvent.bc_company)).label(
                "company_count"
            ),
            func.count(func.distinct(models.BrowserEvent.bc_page_id)).label(
                "page_count"
            ),
        )
        .filter(models.BrowserEvent.user_id == user_id)
        .one()
    )

    # letzte 200 Events des Nutzers
    events = (
        db.query(models.BrowserEvent)
        .filter(models.BrowserEvent.user_id == user_id)
        .order_by(models.BrowserEvent.timestamp.desc())
        .limit(200)
        .all()
    )

    # Top Business Central Seiten (Company + Page-ID) nach Event-Anzahl
    top_pages = (
        db.query(
            models.BrowserEvent.bc_company,
            models.BrowserEvent.bc_page_id,
            models.BrowserEvent.page_title,
            func.count(models.BrowserEvent.id).label("cnt"),
        )
        .filter(models.BrowserEvent.user_id == user_id)
        .group_by(
            models.BrowserEvent.bc_company,
            models.BrowserEvent.bc_page_id,
            models.BrowserEvent.page_title,
        )
        .order_by(desc("cnt"))
        .limit(20)
        .all()
    )

    # Verteilung nach Aktionstyp (click/change/keydown etc.)
    action_stats = (
        db.query(
            models.BrowserEvent.action_type,
            func.count(models.BrowserEvent.id).label("cnt"),
        )
        .filter(models.BrowserEvent.user_id == user_id)
        .group_by(models.BrowserEvent.action_type)
        .order_by(desc("cnt"))
        .all()
    )

    return templates.TemplateResponse(
        "users_detail.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "top_pages": top_pages,
            "action_stats": action_stats,
            "events": events,
        },
    )
