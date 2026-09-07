"""MED V9 — Regras de negócio de autenticação.

Fluxo de aprendizagem do login:
    payload (email/senha) → validação → busca do usuário → verify_password
    → emissão de access/refresh → resposta

O registro centraliza a política de papéis: quem pode ser criado com qual
papel e como o hash é aplicado — routers e demais módulos NÃO repetem isso.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.auth.schemas import RegisterIn
from App.modules.auth.security import (
    ACCESS_TOKEN_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from App.modules.users.models import User


class ValidationError(Exception):
    """Regra de negócio violada (422)."""


class AuthError(Exception):
    """Credenciais inválidas (401 — mensagem genérica, sem vazar detalhe)."""


class ConflictError(Exception):
    """Email já registrado (409)."""


# Papéis que podem ser auto-atribuídos no registro público.
# ADMIN e HOSPITAL não podem se auto-registrar: exigem provisionamento
# administrativo (evita escalação de privilégio por anyone na internet).
SELF_SERVICE_ROLES = {"PATIENT", "DOCTOR"}


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.strip().lower())
        return self.db.scalars(stmt).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def register(self, data: RegisterIn) -> User:
        if data.email and self.get_by_email(data.email) is not None:
            raise ConflictError("Email já registrado")
        if data.role not in SELF_SERVICE_ROLES:
            # Segurança: ADMIN/HOSPITAL/RECEPTIONIST/NURSE não são self-service.
            raise ValidationError(f"Role {data.role} não pode ser auto-registrada")
        user = User(
            full_name=data.full_name.strip(),
            email=data.email.strip().lower(),
            role=data.role,
            # O hash acontece AQUI (service), nunca no router e nunca no banco.
            password_hash=hash_password(data.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> tuple[User, dict]:
        """Autentica e devolve o usuário + o par de tokens.

        Mensagem de erro GENÉRICA tanto para email inexistente quanto senha
        errada: não vazar quais emails existem na base (user enumeration).
        """
        user = self.get_by_email(email)
        if user is None or user.password_hash is None:
            raise AuthError("Credenciais inválidas")
        if not verify_password(password, user.password_hash):
            raise AuthError("Credenciais inválidas")
        tokens = {
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": create_refresh_token(user.id, user.role),
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_MINUTES * 60,
        }
        return user, tokens

    def refresh(self, refresh_token: str) -> dict:
        """Renova o par de tokens a partir de um refresh token válido.

        O refresh token É um JWT, mas com type="refresh": decode_token rejeita
        usá-lo como access (e vice-versa). Novo par completo emitido
        (rotação), limitando a janela de uso de um refresh roubado.
        """
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except Exception as exc:  # TokenError
            raise AuthError(str(exc) or "Refresh token inválido")
        user = self.get_by_id(int(payload["sub"]))
        if user is None:
            # Usuário deletado após emitir o token → token órfão não autentica.
            raise AuthError("Refresh token inválido")
        return {
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": create_refresh_token(user.id, user.role),
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_MINUTES * 60,
        }
