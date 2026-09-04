"""MED V3 — tests for care requests ("Preciso de atendimento")."""

import pytest

from App.modules.users.models import User

VALID_PAYLOAD = {
    "patient_id": 1,
    "reason": "Dor de cabeca persistente",
    "specialty": "Clinica geral",
    "symptoms": "Dor de cabeca ha 3 dias",
    "description": "Dor que piora a tarde",
    "cep": "01310100",
    "referral": "",
    "discomfort_level": 6,
    "symptom_onset": "2026-02-17",
    "notes": "",
}


@pytest.fixture
def patient(db_session) -> User:
    user = User(full_name="Maria Paciente", email="maria@example.com", role="PATIENT")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_care_request(client, patient):
    res = client.post("/api/v1/care-requests", json=VALID_PAYLOAD)
    assert res.status_code == 201
    body = res.json()
    assert body["id"] > 0
    assert body["patient_id"] == patient.id
    assert body["status"] == "CREATED"
    assert body["discomfort_level"] == 6
    assert body["symptom_onset"] == "2026-02-17"
    assert body["cep"] == "01310100"
    assert body["created_at"]


def test_field_validation(client, patient):
    # discomfort_level fora da faixa
    payload = {**VALID_PAYLOAD, "discomfort_level": 11}
    res = client.post("/api/v1/care-requests", json=payload)
    assert res.status_code == 422

    # CEP curto demais
    payload = {**VALID_PAYLOAD, "cep": "123"}
    res = client.post("/api/v1/care-requests", json=payload)
    assert res.status_code == 422

    # motivo muito curto
    payload = {**VALID_PAYLOAD, "reason": "x"}
    res = client.post("/api/v1/care-requests", json=payload)
    assert res.status_code == 422

    # patient_id <= 0
    payload = {**VALID_PAYLOAD, "patient_id": 0}
    res = client.post("/api/v1/care-requests", json=payload)
    assert res.status_code == 422


def test_nonexistent_patient(client, patient):
    payload = {**VALID_PAYLOAD, "patient_id": 9999}
    res = client.post("/api/v1/care-requests", json=payload)
    assert res.status_code == 404
    assert "não encontrado" in res.json()["detail"]


def test_non_patient_user(client, db_session, patient):
    receptionist = User(full_name="Joao Recepcao", email="joao@example.com", role="RECEPTIONIST")
    db_session.add(receptionist)
    db_session.commit()
    db_session.refresh(receptionist)

    payload = {**VALID_PAYLOAD, "patient_id": receptionist.id}
    res = client.post("/api/v1/care-requests", json=payload)
    assert res.status_code == 422
    assert "não é um paciente" in res.json()["detail"]


def test_get_by_id(client, patient):
    created = client.post("/api/v1/care-requests", json=VALID_PAYLOAD).json()
    res = client.get(f"/api/v1/care-requests/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]

    res = client.get("/api/v1/care-requests/9999")
    assert res.status_code == 404


def test_list_by_patient(client, db_session, patient):
    client.post("/api/v1/care-requests", json=VALID_PAYLOAD)
    other = User(full_name="Outro Paciente", email="outro@example.com", role="PATIENT")
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    client.post("/api/v1/care-requests", json={**VALID_PAYLOAD, "patient_id": other.id})

    res = client.get(f"/api/v1/care-requests/patient/{patient.id}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["patient_id"] == patient.id

    # paciente inexistente → lista vazia (paciente_id positivo válido)
    res = client.get("/api/v1/care-requests/patient/4242")
    assert res.status_code == 200
    assert res.json() == []

    # patient_id inválido
    res = client.get("/api/v1/care-requests/patient/0")
    assert res.status_code == 422
