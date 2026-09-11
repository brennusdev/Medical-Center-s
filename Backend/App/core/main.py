"""Medical Center API - application entrypoint."""

#
# ÁREA: PONTO DE ENTRADA DA APLICAÇÃO (core/main.py)
# Responsabilidade: montar o app FastAPI — configuração, middlewares,
# registro de TODOS os routers dos módulos e endpoints de health.
# Fluxo de execução deste arquivo (de cima para baixo):
#   1. imports dos routers de cada módulo (cada módulo expõe 1 router);
#   2. configure_logging() — logging JSON (V12);
#   3. criação do app + CORS;
#   4. include_router de cada módulo, todos sob /api/v1;
#   5. endpoints /health, /health/readiness, /health/liveness;
#   6. middleware de security headers;
#   7. handlers globais de exceção (por último — pegam tudo).
#
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from App.core.config import settings

# MED V12 — infraestrutura: logging estruturado + tratamento global de erros.
from App.core.database import get_db
from App.core.error_handlers import register_exception_handlers
from App.core.health import check_database
from App.core.logging_config import configure_logging
from App.modules.analytics.router import router as analytics_router
from App.modules.appointments.router import router as appointments_router

# MED V10 — auditoria (append-only, consulta ADMIN).
from App.modules.audit.router import router as audit_router
from App.modules.auth.router import router as auth_router
from App.modules.care_requests.router import router as care_requests_router
from App.modules.dashboards.router import router as dashboards_router

# MED V15 — inteligência operacional (somente leitura, sem diagnóstico).
from App.modules.intelligence.router import router as intelligence_router
from App.modules.medical_evaluations.router import router as medical_evaluations_router
from App.modules.notifications.router import router as notifications_router
from App.modules.patient_status.router import router as patient_status_router
from App.modules.queues.router import router as queues_router

# MED V12 — logging estruturado (JSON) configurado uma vez no import do app;
# em modo DEBUG o nível sobe para facilitar desenvolvimento local.
configure_logging(level="DEBUG" if settings.DEBUG else "INFO")  # type: ignore[arg-type]

# ÁREA: INSTANCIAÇÃO DO APP — metadados exibidos no /docs (Swagger).
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="15.0.0",
    description="MED - Medical Center API. V15: inteligência operacional (sem diagnóstico médico).",
)

# ÁREA: CORS — quem pode chamar a API pelo navegador.
# "*" permite qualquer origem (ok em dev); em produção restringir.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ÁREA: REGISTRO DAS ROTAS — cada módulo contribui com um router.
# O prefixo /api/v1 vem de config.API_V1_PREFIX (versionamento de API).
app.include_router(appointments_router, prefix=settings.API_V1_PREFIX)
app.include_router(care_requests_router, prefix=settings.API_V1_PREFIX)
app.include_router(queues_router, prefix=settings.API_V1_PREFIX)
app.include_router(patient_status_router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_evaluations_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
# MED V8 — dashboards e analytics (camada de leitura; sem regras novas de negócio).
app.include_router(dashboards_router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)
# MED V15 — inteligência operacional.
app.include_router(intelligence_router, prefix=settings.API_V1_PREFIX)
# MED V9 — autenticação (JWT, registro, login, refresh).
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
# MED V10 — auditoria.
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)


# ÁREA: HEALTH CHECKS (observabilidade — V12).
@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness simples: a aplicação está executando (não verifica dependências)."""
    return {"status": "ok", "version": "15.0.0"}


# MED V12 — Readiness x Liveness (kubernetes/orquestradores):
# - Liveness (/health): processo vivo. Se falhar, o container é reiniciado.
#   NÃO toca no banco: uma queda momentânea do Postgres não deve causar
#   reinício em cascata da API — reinício não conserta o banco.
# - Readiness (/health/readiness): pronto para receber tráfego. Verifica
#   dependências críticas (banco). Falha tira o pod do balanceador, sem matá-lo.
# O check real vive em App/core/health.py (reuso interno — mesma função usada
# por workers e pela CI), e NUNCA expõe credenciais: só ok + latência.
@app.get("/health/readiness", tags=["health"])
def readiness(db: Session = Depends(get_db)) -> dict:
    result = check_database(db)
    return {"status": "ready" if result["ok"] else "not_ready", **result}


@app.get("/health/liveness", tags=["health"])
def liveness() -> dict:
    return {"status": "alive"}


# MED V9 — Security headers na resposta de qualquer rota.
# Middleware simples (em vez de biblioteca externa): o MED é uma API JSON,
# então os cabeçalhos relevantes são os de hardening básico de APIs.
# - X-Content-Type-Options: evita sniffing de conteúdo;
# - X-Frame-Options/DENY: a API nunca deve ser embutida em iframe;
# - Referrer-Policy: não vazar URLs (que podem conter ids) para terceiros.
# CORS permanece configurado acima; em produção, restringir allow_origins.
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from starlette.responses import Response  # noqa: E402


# ÁREA: SECURITY HEADERS (hardening — V9).
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response


app.add_middleware(SecurityHeadersMiddleware)

# ÁREA: ERROS GLOBAIS — registrado por último para envolver tudo.
# MED V12 — handlers globais de exceção por último: padronizam o envelope de
# erro {error, message, request_id} e escondem stack trace em produção.
register_exception_handlers(app)
