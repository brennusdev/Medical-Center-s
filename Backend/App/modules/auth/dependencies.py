"""MED V9 — Dependencies reutilizáveis de autenticação/autorização.

Por que dependencies: a lógica de autenticação fica em UM lugar; routers
apenas declaram o que exigem (role/ownership) sem reimplementar JWT.

Fluxo de autorização (documentado):
    Request → JWT → Current User → Role → Permission → Resource Ownership → Service

MODO LEGADO (ALLOW_LEGACY_AUTH=True, default nesta transição):
- Sem header Authorization, get_current_user devolve None e as rotas antigas
  continuam funcionando com ids explícitos (compatibilidade V1–V8 e testes).
- COM header Authorization, o JWT é SEMPRE validado — tokens inválidos falham
  mesmo em modo legado (nunca aceitamos um token ruim).
- Em produção ALLOW_LEGACY_AUTH=False → require_role exige token válido.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from App.core.config import settings
from App.core.database import get_db
from App.modules.auth.security import TokenError, decode_token
from App.modules.users.models import User

# Papéis de domínio autorizados a atuar sobre filas/prioridades (herdado da V4).
DOMAIN_ACTOR_ROLES = {"RECEPTIONIST", "NURSE", "DOCTOR", "ADMIN"}


def _extract_bearer(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User | None:
    """Resolve o usuário do token; None quando não há token (modo legado).

    Erros de token SEMPRE viram 401 — um token presente e inválido nunca é
    ignorado, mesmo em modo legado.
    """
    token = _extract_bearer(request)
    if token is None:
        return None
    try:
        payload = decode_token(token, expected_type="access")
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    user = db.get(User, int(payload["sub"]))
    if user is None:
        # Usuário deletado com token ainda válido → não autentica.
        raise HTTPException(status_code=401, detail="Usuário do token não existe")
    return user


def require_role(*roles: str):
    """Dependency factory: exige um dos papéis informados.

    Uso em router:
        @router.get(..., dependencies=[Depends(require_role("ADMIN"))])

    - Sem token: 401 quando legacy desabilitado; None-user aceito em legacy
      (compatibilidade), para que V1–V8 e testes não quebrem.
    - Com token: role deve estar na lista (403 caso contrário).
    """

    def dependency(user: User | None = Depends(get_current_user)) -> User | None:
        if user is None:
            if settings.ALLOW_LEGACY_AUTH:
                return None  # modo de transição: comportamento V8 preservado
            raise HTTPException(status_code=401, detail="Autenticação obrigatória")
        if roles and user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requer papel {sorted(roles)}")
        return user

    return dependency


def require_permission(permission: str):
    """Dependency factory por permissão nomeada (RBAC coarse-grained).

    Mapa explícito de permissões → papéis. Manter aqui (não espalhado nos
    routers) para auditar a matriz de acesso em um só lugar.
    """
    PERMISSIONS: dict[str, set[str]] = {
        "queues.priority.update": {"RECEPTIONIST", "NURSE", "DOCTOR", "ADMIN"},
        "medical_evaluation.create": {"DOCTOR", "NURSE", "RECEPTIONIST", "ADMIN"},
        "patient_status.create": {"PATIENT"},
        "care_request.create": {"PATIENT"},
        "audit.read": {"ADMIN"},
        "dashboard.admin": {"ADMIN"},
        "dashboard.hospital": {"HOSPITAL", "ADMIN"},
    }

    def dependency(user: User | None = Depends(get_current_user)) -> User | None:
        if user is None:
            if settings.ALLOW_LEGACY_AUTH:
                return None
            raise HTTPException(status_code=401, detail="Autenticação obrigatória")
        allowed = PERMISSIONS.get(permission, set())
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail=f"Permissão exigida: {permission}")
        return user

    return dependency


# Tipo anotado para injeção limpa nos routers.
CurrentUser = Annotated[User | None, Depends(get_current_user)]


def check_ownership(user: User | None, resource_user_id: int, *, legacy_fallback: bool = True) -> None:
    """Verificação de RESOURCE OWNERSHIP.

    Regra: role diz o que o usuário pode fazer; ownership verifica EM QUAL
    recurso ele pode fazer. Um PATIENT autenticado só acessa os próprios
    recursos (resource_user_id == user.id); ADMIN acessa qualquer um.
    Com token presente e dono diferente → 403. Sem token em modo legado →
    permitido (compatibilidade V8), documentado como débito de transição.
    """
    if user is None:
        if legacy_fallback and settings.ALLOW_LEGACY_AUTH:
            return
        raise HTTPException(status_code=401, detail="Autenticação obrigatória")
    if user.role == "ADMIN":
        return
    if user.id != resource_user_id:
        raise HTTPException(status_code=403, detail="Você não tem acesso a este recurso")
