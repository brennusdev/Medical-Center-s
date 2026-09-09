"""Medical Center API - application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from App.core.config import settings
from App.modules.analytics.router import router as analytics_router
# MED V10 — auditoria (append-only, consulta ADMIN).
from App.modules.audit.router import router as audit_router
from App.modules.appointments.router import router as appointments_router
from App.modules.auth.router import router as auth_router
from App.modules.care_requests.router import router as care_requests_router
from App.modules.dashboards.router import router as dashboards_router
from App.modules.queues.router import router as queues_router
from App.modules.medical_evaluations.router import router as medical_evaluations_router
from App.modules.notifications.router import router as notifications_router
from App.modules.patient_status.router import router as patient_status_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="10.0.0",
    description="MED - Medical Center API. V10: auditoria append-only (actor, action, recurso, valores).",
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
# MED V9 — autenticação (JWT, registro, login, refresh).
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
# MED V10 — auditoria.
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": "10.0.0"}


# MED V9 — Security headers na resposta de qualquer rota.
# Middleware simples (em vez de biblioteca externa): o MED é uma API JSON,
# então os cabeçalhos relevantes são os de hardening básico de APIs.
# - X-Content-Type-Options: evita sniffing de conteúdo;
# - X-Frame-Options/DENY: a API nunca deve ser embutida em iframe;
# - Referrer-Policy: não vazar URLs (que podem conter ids) para terceiros.
# CORS permanece configurado acima; em produção, restringir allow_origins.
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from starlette.responses import Response  # noqa: E402


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


app.add_middleware(SecurityHeadersMiddleware)
