"""Medical Center API - application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from App.core.config import settings
from App.modules.appointments.router import router as appointments_router
from App.modules.care_requests.router import router as care_requests_router
from App.modules.queues.router import router as queues_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="4.0.0",
    description="MED - Medical Center API. V4: filas e priorização operacional (não clínica).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointments_router, prefix=settings.API_V1_PREFIX)
app.include_router(care_requests_router, prefix=settings.API_V1_PREFIX)
app.include_router(queues_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": "4.0.0"}
