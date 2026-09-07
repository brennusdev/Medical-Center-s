"""MED V9 — Contratos Pydantic do domínio auth.

Nota de segurança: os schemas de SAÍDA nunca expõem `password_hash`.
`UserRead` lista explicitamente os campos permitidos (allowlist) — usar
`from_attributes` com o model inteiro vazaría o hash.
"""

import re

from pydantic import BaseModel, field_validator

# Perfis da V9. RECEPTIONIST/NURSE permanecem aceitos (legados da V4) para
# não quebrar os fluxos de prioridade já existentes.
ALLOWED_ROLES = {"PATIENT", "DOCTOR", "HOSPITAL", "ADMIN", "RECEPTIONIST", "NURSE"}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterIn(BaseModel):
    """Payload de registro.

    Regras: senha mínima de 8 caracteres (validação de entrada — não confiamos
    no cliente); role restrita à allowlist (evita criar papéis arbitrários).
    """

    full_name: str
    email: str
    password: str
    role: str = "PATIENT"

    @field_validator("full_name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not 2 <= len(v) <= 150:
            raise ValueError("full_name deve ter entre 2 e 150 caracteres")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("email inválido")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        # Mínimo de tamanho; complexidade rígida reduz usabilidade sem ganho
        # real quando o hash já é forte (PBKDF2 600k + sal).
        if len(v) < 8:
            raise ValueError("password deve ter no mínimo 8 caracteres")
        return v

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in ALLOWED_ROLES:
            raise ValueError(f"role deve ser uma de {sorted(ALLOWED_ROLES)}")
        return v


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    """Par access/refresh emitido no login e na renovação."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos de validade do access token


class UserRead(BaseModel):
    """Perfil público do usuário — allowlist de campos (sem password_hash)."""

    id: int
    full_name: str
    email: str
    role: str
