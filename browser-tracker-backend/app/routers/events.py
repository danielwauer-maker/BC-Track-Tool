# app/routers/events.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from ..deps import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/events", tags=["events"])


def get_or_create_user(db: Session, external_id: str | None):
    if not external_id:
        return None
    user = db.query(models.User).filter(models.User.external_id == external_id).first()
    if not user:
        user = models.User(external_id=external_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_or_create_session(db: Session, user, session_key: str | None,
                          client_ip: str | None, user_agent: str | None):
    if not session_key:
        # Fallback: eine generische Session pro User ohne Key
        session = models.Session(
            user_id=user.id if user else None,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    session = (
        db.query(models.Session)
        .filter(
            models.Session.session_key == session_key,
            models.Session.user_id == (user.id if user else None),
        )
        .order_by(models.Session.started_at.desc())
        .first()
    )
    if not session:
        session = models.Session(
            user_id=user.id if user else None,
            session_key=session_key,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


@router.post("/batch", response_model=list[schemas.BrowserEvent])
async def create_events_batch(
    request: Request,
    events: List[schemas.BrowserEventCreate],
    db: Session = Depends(get_db),
):

    print(f"[EVENTS] Batch erhalten: {len(events)} Events")  # <--- NEU
    
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    created_events: list[models.BrowserEvent] = []

    # Annahme: Alle Events im Batch gehören zum selben User & Session
    user_external_id = events[0].user_external_id if events else None
    session_key = events[0].session_key if events else None

    user = get_or_create_user(db, user_external_id) if user_external_id else None
    session = get_or_create_session(db, user, session_key, client_ip, user_agent)

    for ev in events:
        ts = ev.timestamp
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)

        db_event = models.BrowserEvent(
            session_id=session.id if session else None,
            timestamp=ts.astimezone(timezone.utc),
            user_id=user.id if user else None,
            page_url=ev.page_url,
            page_title=ev.page_title,
            element_type=ev.element_type,
            element_role=ev.element_role,
            element_label=ev.element_label,
            element_name=ev.element_name,
            element_id=ev.element_id,
            element_path=ev.element_path,
            action_type=ev.action_type,
            old_value=ev.old_value,
            new_value=ev.new_value,
            meta=ev.meta,
        )
        db.add(db_event)
        created_events.append(db_event)

    db.commit()
    for e in created_events:
        db.refresh(e)

    return created_events
