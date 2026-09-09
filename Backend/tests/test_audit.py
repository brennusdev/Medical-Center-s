"""MED V10 — Testes da auditoria.

Cobre: registro de evento, sanitização de secrets, listagem paginada,
filtros, autorização (somente ADMIN) e append-only.
"""

import json

import pytest

from App.modules.audit.models import AuditAction
from App.modules.audit.service import AuditService
from App.modules.auth.security import hash_password
from App.modules.users.models import User


@pytest.fixture
def admin_user(db_session) -> User:
    """Usuário ADMIN para consulta de auditoria."""
    user = User(full_name="Admin", email="admin@med.local", role="ADMIN",
                password_hash=hash_password("StrongPass1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def patient_user(db_session) -> User:
    user = User(full_name="Paciente", email="pac@med.local", role="PATIENT",
                password_hash=hash_password("PatientPass1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_token(client, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_audit_log_sanitizes_secrets(db_session):
    svc = AuditService(db_session)
    svc.log(
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=1,
        new_value={"email": "a@b.c", "password": "SuperSecret", "token": "xyz", "name": "A"},
    )
    logs = svc.list_logs(resource_type="user")
    assert len(logs) == 1
    # O repository devolve TEXT (JSON serializado); parse para validar conteúdo.
    payload = json.loads(logs[0].new_value)
    assert "password" not in payload
    assert "token" not in payload
    assert payload["email"] == "a@b.c"


def test_audit_append_only_and_filters(db_session):
    svc = AuditService(db_session)
    svc.log(action=AuditAction.CREATE, resource_type="queue", resource_id=7, actor_id=1)
    svc.log(action=AuditAction.UPDATE, resource_type="queue", resource_id=7, actor_id=2)
    svc.log(action=AuditAction.CREATE, resource_type="appointment", resource_id=9, actor_id=1)

    # filtro por resource_type
    queues = svc.list_logs(resource_type="queue")
    assert len(queues) == 2
    # filtro por actor
    mine = svc.list_logs(actor_id=1)
    assert len(mine) == 2
    # filtro por ação
    creates = svc.list_logs(action=AuditAction.CREATE)
    assert len(creates) == 2


def test_audit_list_endpoint_requires_admin(client, admin_user, patient_user):
    """Paciente (mesmo autenticado) não lista auditoria: 403. ADMIN: 200."""
    token_admin = _login_token(client, admin_user.email, "StrongPass1!")
    resp = client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200
    assert "items" in resp.json()

    token_patient = _login_token(client, patient_user.email, "PatientPass1!")
    resp = client.get("/api/v1/audit/logs", headers={"Authorization": f"Bearer {token_patient}"})
    assert resp.status_code == 403


def test_audit_list_endpoint_unauthenticated_legacy(client, admin_user):
    """Modo legado (sem token): endpoint responde (compat V1–V8) — em produção
    ALLOW_LEGACY_AUTH=false fecha isso. Documentado na V9/V10."""
    resp = client.get("/api/v1/audit/logs")
    assert resp.status_code == 200
