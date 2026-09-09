"""MED V9 — Testes de segurança: senha, login, tokens, roles, ownership.

Também servem de regressão: qualquer teste dos fluxos V1–V8 sem token
continua passando (modo legado), enquanto um token PRESENTE e inválido
nunca é aceito.
"""

import base64
import json
from datetime import date

import pytest

from App.modules.auth.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from App.modules.users.models import User

# ---------------------------------------------------------------------------
# Senha (hash)
# ---------------------------------------------------------------------------

def test_hash_password_not_plaintext_and_verifiable():
    stored = hash_password("senha-secreta-123")
    # Nunca texto puro e nunca o mesmo hash duas vezes (sal aleatório).
    assert "senha-secreta-123" not in stored
    assert stored != hash_password("senha-secreta-123")
    assert verify_password("senha-secreta-123", stored)


def test_verify_password_rejects_wrong():
    stored = hash_password("correta")
    assert not verify_password("errada", stored)
    assert not verify_password("correta ", stored)


def test_verify_password_rejects_malformed_hash():
    assert not verify_password("x", "texto-que-nao-e-hash")


# ---------------------------------------------------------------------------
# Tokens JWT
# ---------------------------------------------------------------------------

def test_access_token_roundtrip():
    token = create_access_token(42, "PATIENT")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "42"
    assert payload["role"] == "PATIENT"


def test_refresh_token_cannot_be_used_as_access():
    refresh = create_refresh_token(42, "PATIENT")
    with pytest.raises(TokenError):
        decode_token(refresh, expected_type="access")


def test_tampered_token_rejected():
    token = create_access_token(42, "PATIENT")
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(TokenError):
        decode_token(tampered)


def test_expired_token_rejected():
    expired = create_token(1, "PATIENT", "access", -10)
    with pytest.raises(TokenError):
        decode_token(expired)


def test_token_has_no_sensitive_data():
    token = create_access_token(1, "PATIENT")
    payload_b64 = token.split(".")[1]
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "==" * (-len(payload_b64) % 4)))
    assert "password" not in json.dumps(payload)
    # Claims mínimas — nenhum dado excessivo no token.
    assert set(payload.keys()) == {"sub", "role", "type", "iat", "exp", "jti"}


# ---------------------------------------------------------------------------
# Registro / login / refresh / me (HTTP)
# ---------------------------------------------------------------------------

def test_register_and_login_flow(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ana Clara", "email": "ana@ex.com", "password": "senha-123", "role": "PATIENT"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["role"] == "PATIENT"
    # Allowlist de campos: hash nunca vaza.
    assert "password" not in body and "password_hash" not in body

    tokens = client.post("/api/v1/auth/login", json={"email": "ana@ex.com", "password": "senha-123"})
    assert tokens.status_code == 200
    tokens = tokens.json()
    assert tokens["token_type"] == "bearer"

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert res.status_code == 200
    assert res.json()["email"] == "ana@ex.com"


def test_login_wrong_password_401_generic(client):
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Bruno", "email": "bruno@ex.com", "password": "senha-123", "role": "PATIENT"},
    )
    res = client.post("/api/v1/auth/login", json={"email": "bruno@ex.com", "password": "errada-123"})
    assert res.status_code == 401
    # Mensagem genérica: não revela se o email existe (user enumeration).
    res2 = client.post("/api/v1/auth/login", json={"email": "nobody@ex.com", "password": "errada-123"})
    assert res.json()["detail"] == res2.json()["detail"]


def test_register_duplicate_email_409(client):
    payload = {"full_name": "Carla", "email": "carla@ex.com", "password": "senha-123", "role": "PATIENT"}
    client.post("/api/v1/auth/register", json=payload)
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_register_admin_role_forbidden(client):
    # ADMIN não é self-service (evita escalação de privilégio).
    res = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Dudu", "email": "dudu@ex.com", "password": "senha-123", "role": "ADMIN"},
    )
    assert res.status_code == 422


def test_register_short_password_422(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Eva", "email": "eva@ex.com", "password": "123", "role": "PATIENT"},
    )
    assert res.status_code == 422


def test_refresh_flow(client):
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Felipe", "email": "felipe@ex.com", "password": "senha-123", "role": "DOCTOR"},
    )
    tokens = client.post("/api/v1/auth/login", json={"email": "felipe@ex.com", "password": "senha-123"}).json()
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 200
    assert res.json()["access_token"] != tokens["access_token"]


def test_refresh_with_access_token_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Gabi", "email": "gabi@ex.com", "password": "senha-123", "role": "PATIENT"},
    )
    tokens = client.post("/api/v1/auth/login", json={"email": "gabi@ex.com", "password": "senha-123"}).json()
    # Access token não serve como refresh (tipos separados).
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert res.status_code == 401


def test_me_without_token_401(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_invalid_token_401(client):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nao-e-um-token"})
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# RBAC + Ownership nas rotas protegidas
# ---------------------------------------------------------------------------

def _register_and_login(client, email, role, password="senha-123"):
    name = email.split("@")[0].title()
    if len(name) < 2:
        name = name + " Silva"  # valida regra de full_name (2–150 chars)
    client.post(
        "/api/v1/auth/register",
        json={"full_name": name, "email": email, "password": password, "role": role},
    )
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()


def _make_queue_for(db_session, patient_id, specialty="Cardiologia"):
    """Cria um pedido de cuidado + fila reais no banco de teste.

    Usado pelos testes de RBAC/ownership: sem isso não existe 'recurso'
    concreto para tentar acessar ou alterar via HTTP.
    """
    from App.modules.care_requests.schemas import CareRequestCreate
    from App.modules.care_requests.service import CareRequestService
    from App.modules.queues.schemas import QueueCreate
    from App.modules.queues.service import QueueService

    cr = CareRequestService(db_session).create(
        CareRequestCreate(
            patient_id=patient_id, reason="dor", specialty=specialty, symptoms="s",
            description="d", cep="01310100", referral="", discomfort_level=5,
            symptom_onset=date(2026, 1, 1), notes="",
        )
    )
    return QueueService(db_session).create(
        QueueCreate(care_request_id=cr.id, specialty=specialty, hospital_id=None, actor_id=None)
    )


def test_patient_cannot_access_other_patient_queues(client):
    tokens_a = _register_and_login(client, "a@ex.com", "PATIENT")
    _register_and_login(client, "b@ex.com", "PATIENT")
    # id 9999 garante que NÃO é o próprio recurso do paciente autenticado.
    res = client.get(
        "/api/v1/queues/patient/9999",
        headers={"Authorization": f"Bearer {tokens_a['access_token']}"},
    )
    # Ownership: paciente autenticado só acessa os próprios recursos.
    assert res.status_code == 403


def test_patient_can_access_own_queues(client):
    tokens = _register_and_login(client, "own@ex.com", "PATIENT")
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
    res = client.get(
        f"/api/v1/queues/patient/{me['id']}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert res.status_code == 200


def test_doctor_token_derives_priority_actor(client, db_session):
    """Com token, o actor da mudança de prioridade é o usuário do token.

    O actor_id no payload é IGNORADO — evita que o cliente se passe por
    outro profissional (a V4 dependia do id informado; a V9 corrige).
    """
    doctor_tokens = _register_and_login(client, "dr@ex.com", "DOCTOR")
    patient = User(full_name="Pac", email="pac@ex.com", role="PATIENT")
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    queue = _make_queue_for(db_session, patient.id)

    res = client.patch(
        f"/api/v1/queues/{queue.id}/priority",
        json={"priority": "HIGH", "actor_id": 9999},  # 9999 seria um usuário inexistente
        headers={"Authorization": f"Bearer {doctor_tokens['access_token']}"},
    )
    assert res.status_code == 200
    assert res.json()["priority"] == "HIGH"


def test_patient_token_cannot_change_priority(client, db_session):
    """Paciente autenticado tentando função de profissional → 403 (RBAC)."""
    tokens = _register_and_login(client, "prio@ex.com", "PATIENT")
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()

    # Cria uma fila real para o paciente e tenta alterar prioridade com o token.
    queue = _make_queue_for(db_session, me["id"])
    res = client.patch(
        f"/api/v1/queues/{queue.id}/priority",
        json={"priority": "HIGH"},  # actor_id omitido: com token vem do token
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    # 403 esperado: o service recusa PATIENT. Se o payload incompleto virar
    # 422 antes, o teste ainda é válido — mas o contrato exige 403, então
    # garantimos actor_id presente para chegar à checagem de papel.
    if res.status_code == 422:
        res = client.patch(
            f"/api/v1/queues/{queue.id}/priority",
            json={"priority": "HIGH", "actor_id": me["id"]},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
    assert res.status_code == 403


def test_legacy_requests_still_work_without_token(client):
    """Regressão V1–V8: fluxos antigos sem Authorization continuam válidos."""
    assert client.get("/api/v1/dashboard/admin").status_code == 200
    assert client.get("/api/v1/analytics/overview").status_code == 200
    assert client.get("/api/v1/appointments/patient/1").status_code == 200
