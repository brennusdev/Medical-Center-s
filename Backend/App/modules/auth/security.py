"""MED V9 — Primitivas de segurança (hash de senha e JWT HS256).

HASH vs ENCRYPTION (diferença fundamental, por isso hash):
- Encryption é REVERSÍVEL: com a chave, alguém recupera a senha original.
- Hash é IRREVERSÍVEL: do hash não se recupera a senha; a verificação compara
  o hash da tentativa com o hash armazenado. Assim, mesmo que o banco vaze,
  as senhas originais não são expostas.
- Nunca armazenamos a senha em texto puro, nunca "criptografamos" senha e
  nunca usamos hash SEM sal (rainbow tables).

PBKDF2-HMAC-SHA256 (stdlib hashlib):
- sal aleatório por senha (16 bytes) → duas senhas iguais geram hashes diferentes;
- 600.000 iterações (OWASP 2023 recomenda ≥600k para PBKDF2-SHA256) — torna a
  força bruta cara para atacantes, sem inviabilizar o login legítimo;
- formato armazenado: "pbkdf2_sha256$iterações$salt_hex$hash_hex" — permite
  subir iterações no futuro sem invalidar hashes existentes (upgrade por login).

JWT (HS256 manual com hmac stdlib):
- tokens assinados com secret do servidor; payload NÃO é criptografado —
  qualquer pessoa decodifica o payload; por isso o token contém APENAS
  identificadores (sub, role, tipo, exp). Nunca dados sensíveis, senha ou
  permissões detalhadas.
- Riscos documentados: token roubado é válido até expirar (mitigação: expiração
  curta do access token + refresh token); revogação imediata não é possível sem
  state no servidor (fora do escopo da V10); o secret DEVE vir de configuração
  de ambiente, nunca de código.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from App.core.config import settings

# Parâmetros de hashing — constants nomeadas para estudo/ajuste centralizado.
PBKDF2_ITERATIONS = 600_000
PBKDF2_SALT_BYTES = 16
PBKDF2_HASH_NAME = "sha256"

# Duração dos tokens em segundos.
ACCESS_TOKEN_MINUTES = 30
REFRESH_TOKEN_DAYS = 7


def hash_password(password: str) -> str:
    """Gera o hash com sal único. Nunca guardamos a senha original.

    O sal aleatório por senha é o que impede que dois usuários com a mesma
    senha tenham o mesmo hash (e que tabelas pré-computadas funcionem).
    """
    salt = os.urandom(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_HASH_NAME, password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_{PBKDF2_HASH_NAME}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verifica a senha contra o hash armazenado.

    Usa hmac.compare_digest (comparação em tempo constante) para evitar
    timing attacks — comparação com == pode vazar informação por tempo.
    Se o hash não tem o formato esperado (ex.: legado), falha fechado (False).
    """
    try:
        algo_part, iterations_s, salt_hex, hash_hex = stored.split("$")
        iterations = int(iterations_s)
    except (ValueError, AttributeError):
        return False
    if not algo_part.startswith("pbkdf2_"):
        return False
    digest = hashlib.pbkdf2_hmac(
        algo_part.removeprefix("pbkdf2_"),
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        iterations,
    )
    return hmac.compare_digest(digest.hex(), hash_hex)


# -- JWT (HS256) ---------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(subject: str | int, role: str, token_type: str, expires_seconds: int) -> str:
    """Cria um JWT HS256 assinado com o secret configurado.

    Claims mínimas (menos dados no token = menos risco se vazar):
    - sub: id do usuário (string, padrão JWT);
    - role: perfil (PATIENT/DOCTOR/HOSPITAL/ADMIN) — autorização coarse;
    - type: "access" ou "refresh" — um refresh NUNCA deve valer como access;
    - iat/exp: emissão e expiração (epoch, verificação local e barata).
    """
    now = int(time.time())
    payload = {
        "sub": str(subject),
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_seconds,
        # jti: id único do token. Garante que dois tokens emitidos no mesmo
        # segundo sejam diferentes (rotação visível) e prepara revogação
        # futura por lista de jti (state).
        "jti": secrets.token_hex(8),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    segments = (
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    )
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(
        settings.SECRET_KEY.encode(), signing_input, hashlib.sha256
    ).digest()
    return ".".join(segments) + "." + _b64url_encode(signature)


def create_access_token(user_id: int, role: str) -> str:
    return create_token(user_id, role, "access", ACCESS_TOKEN_MINUTES * 60)


def create_refresh_token(user_id: int, role: str) -> str:
    return create_token(user_id, role, "refresh", REFRESH_TOKEN_DAYS * 86400)


class TokenError(Exception):
    """Token inválido, expirado, malformado ou de tipo errado."""


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Valida assinatura, expiração e tipo; devolve as claims.

    Ordem das checagens (falha fechada em qualquer uma):
    1. estrutura de 3 segmentos;
    2. assinatura HMAC (comparação em tempo constante);
    3. expiração;
    4. tipo esperado (access vs refresh) — evita usar refresh no lugar de access.
    """
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError:
        raise TokenError("Token malformado")
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode(), signing_input, hashlib.sha256
    ).digest()
    if not hmac.compare_digest(expected_sig, _b64url_decode(signature_b64)):
        raise TokenError("Assinatura inválida")
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except ValueError:
        raise TokenError("Payload inválido")
    if payload.get("exp", 0) < time.time():
        raise TokenError("Token expirado")
    if payload.get("type") != expected_type:
        raise TokenError("Tipo de token inválido")
    return payload


def generate_reset_secret() -> str:
    """Segredo aleatório de uso geral (ex.: dados de teste/sessão pontual)."""
    return secrets.token_urlsafe(32)
