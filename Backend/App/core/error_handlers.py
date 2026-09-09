"""MED V12 — Tratamento global de exceções.

Responsabilidade:
- Padronizar TODAS as respostas de erro da API no formato:
  {"error": "<tipo>", "message": "<mensagem>", "request_id": "..."}
- Em produção (DEBUG=false), erros inesperados NUNCA expõem stack trace nem
  detalhes internos — o cliente recebe mensagem genérica e o detalhe fica
  no application log correlacionado pelo request_id.

Por que handlers globais?
- Sem eles, cada rota repetiria try/except e algumas respostas vazariam
  estrutura interna. Centralizando, o contrato de erro fica único e testável.
"""

import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("med.api")


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers no app (chamado no core/main.py)."""

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        """Gera um request_id por requisição para correlacionar log ↔ erro.

        O cliente também recebe o header — em caso de bug, o relatório do
        usuário aponta direto para o registro no application log.
        """
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        # 422 padrão FastAPI, mas com envelope padronizado; os detalhes de
        # campo falam sobre o PRÓPRIO request do cliente, não sobre o sistema.
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "Dados inválidos.",
                "details": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        # COMPATIBILIDADE V1–V10: mantemos `detail` (contrato original do
        # FastAPI consumido pelo frontend/mobile e pelos testes de regressão)
        # e ADICIONAMOS o envelope padronizado da V12. Romper `detail` agora
        # quebraria clientes em produção — a padronização é aditiva.
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": str(exc.detail),
                "error": "http_error",
                "message": str(exc.detail),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_handler(request: Request, exc: SQLAlchemyError):
        # Erro de banco: loga completo (técnicos) e devolve mensagem genérica —
        # nomes de tabelas/constraints não são informação pública.
        logger.error("Database error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "Erro interno do servidor.",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        # Última linha de defesa: stack trace só no log, nunca na resposta.
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "message": "Erro interno do servidor.",
                "request_id": getattr(request.state, "request_id", None),
            },
        )
