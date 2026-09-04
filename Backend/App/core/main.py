"""Medical Center API - application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from App.core.config import settings
from App.modules.appointments.router import router as appointments_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="MED - Medical Center API. V2: consultas e agendamentos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointments_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": "2.0.0"}
