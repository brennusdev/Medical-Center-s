#
# ÁREA: MÓDULO AUTH — CAMADA DE ROTAS (auth/router.py)
# Arquitetura do módulo: router (HTTP) → service (regras) → models (banco).
# Este arquivo só mapeia exceções de negócio → códigos HTTP; nenhuma regra
# de auth mora aqui.
#
"""MED V9 — Router de autenticação.

Endpoints:
- POST /auth/register — auto-registro (apenas PATIENT/DOCTOR)
- POST /auth/login    — emite access + refresh
- POST /auth/refresh  — renova o par
- GET  /auth/me       — perfil do usuário do token

Segurança aplicada aqui (nada de regra no transporte além do mapeamento de
exceções → status HTTP):
- 401 com mensagem genérica no login (sem user enumeration);
- hash de senha somente no service;
- /auth/me deriva o usuário do TOKEN, nunca de um id informado pelo cliente.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.auth.dependencies import CurrentUser
from App.modules.auth.schemas import LoginIn, RefreshIn, RegisterIn, TokenOut, UserRead
from App.modules.auth.service import AuthError, AuthService, ConflictError, ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=UserRead, status_code=201, summary="Registrar usuário (PATIENT/DOCTOR)")
def register(payload: RegisterIn, service: AuthService = Depends(get_service)):
    try:
        return service.register(payload)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/login", response_model=TokenOut, summary="Autenticar e receber tokens")
def login(payload: LoginIn, service: AuthService = Depends(get_service)):
    try:
        _, tokens = service.login(payload.email, payload.password)
        return tokens
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/refresh", response_model=TokenOut, summary="Renovar par de tokens")
def refresh(payload: RefreshIn, service: AuthService = Depends(get_service)):
    try:
        return service.refresh(payload.refresh_token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.get("/me", response_model=UserRead, summary="Perfil do usuário autenticado")
def me(user: CurrentUser):
    # O usuário vem SEMPRE do token (nunca de um id do cliente) — regra de
    # "autenticação do paciente derivada do usuário autenticado" da V9.
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticação obrigatória")
    return user
