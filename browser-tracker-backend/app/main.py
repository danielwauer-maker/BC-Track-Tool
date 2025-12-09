from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import events, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Browser Activity Tracker Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # zum Start offen, später einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(events.router)
app.include_router(dashboard.router)
