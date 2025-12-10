# app/schemas.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class BrowserEventBase(BaseModel):
    timestamp: datetime
    user_external_id: Optional[str] = None
    session_key: Optional[str] = None

    page_url: str
    page_title: Optional[str] = None

    bc_page_id: int | None = None    # NEU
    bc_company: str | None = None    # NEU

    element_type: Optional[str] = None
    element_role: Optional[str] = None
    element_label: Optional[str] = None
    element_name: Optional[str] = None
    element_id: Optional[str] = None
    element_path: Optional[str] = None

    action_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    meta: Optional[Dict[str, Any]] = None


class BrowserEventCreate(BrowserEventBase):
    pass


class BrowserEvent(BrowserEventBase):
    id: int

    class Config:
        orm_mode = True


class StatsOverview(BaseModel):
    total_events: int
    total_users: int
    total_sessions: int
    events_last_24h: int
    top_users: List[Dict[str, Any]]
    top_pages: List[Dict[str, Any]]
