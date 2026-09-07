"""Medical Center API - application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from App.core.config import settings
from App.modules.analytics.router import router as analytics_router
from App.modules.appointments.router import router as appointments_router
from App.modules.care_requests.router import router as care_requests_router
from App.modules.dashboards.router import router as dashboards_router
from App.modules.queues.router import router as queues_router
from App.modules.medical_evaluations.router import router as medical_evaluations_router
from App.modules.notifications.router import router as notifications_router
from App.modules.patient_status.router import router as patient_status_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="7.0.0",
    description="MED - Medical Center API. V7: notificações de eventos do atendimento.",
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
app.include_router(patient_status_router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_evaluations_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
# MED V8 — dashboards e analytics (camada de leitura; sem regras novas de negócio).
app.include_router(dashboards_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": "7.0.0"}
