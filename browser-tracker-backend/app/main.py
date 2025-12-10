# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import events, dashboard, dashboard_users  # ggf. anpassen
from .database import engine, Base  # falls du so etwas hast

# DB-Tabellen anlegen (falls noch nicht)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Browser Activity Tracker Backend")

# 🔴 WICHTIG: CORS erlauben, sonst scheitert der Fetch aus dem BC-Tab
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # zum Testen alles erlauben
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# optional: Templates
templates = Jinja2Templates(directory="app/templates")

# Static Files, falls genutzt
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Simple Ping-Endpoint zum Testen
@app.get("/ping")
async def ping(request: Request):
    return {"status": "ok"}


# Router einbinden
app.include_router(events.router)
app.include_router(dashboard.router)
app.include_router(dashboard_users.router)
