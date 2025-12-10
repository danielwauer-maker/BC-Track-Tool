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
    Detailansicht für einen Nutzer: letzte Events, Basisinfos.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # letzte 200 Events des Nutzers
    events = (
        db.query(models.BrowserEvent)
        .filter(models.BrowserEvent.user_id == user_id)
        .order_by(models.BrowserEvent.timestamp.desc())
        .limit(200)
        .all()
    )

    return templates.TemplateResponse(
        "users_detail.html",
        {
            "request": request,
            "user": user,
            "events": events,
        },
    )
