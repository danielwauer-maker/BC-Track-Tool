# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import events, dashboard

# DB-Tabellen erstellen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Browser Activity Tracker Backend")

# Static Files & Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(events.router)
app.include_router(dashboard.router)
