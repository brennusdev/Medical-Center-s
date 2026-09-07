"""MED V5 — tests for patient status updates ("Meu Estado")."""

import pytest

from App.modules.users.models import User

CARE_REQUEST_PAYLOAD = {
    "patient_id": 1,
    "reason": "Dor de cabeca persistente",
    "specialty": "Cardiologia",
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
    user = User(full_name="Maria Paciente", email="maria5@example.com", role="PATIENT")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_patient(db_session) -> User:
    user = User(full_name="Joao Outro", email="joao5@example.com", role="PATIENT")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_care_request(client, patient_id: int) -> int:
    res = client.post(
        "/api/v1/care-requests", json={**CARE_REQUEST_PAYLOAD, "patient_id": patient_id}
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _create_status(client, patient_id, care_request_id, **overrides):
    payload = {
        "patient_id": patient_id,
        "care_request_id": care_request_id,
        "state": "STABLE",
        "symptoms": "Cansaco",
        "severity": 4,
        "description": "Mesmo quadro",
        "notes": "",
        **overrides,
    }
    return client.post("/api/v1/patient-status", json=payload)


# -- criação -------------------------------------------------------------------


def test_create_status_update(client, patient):
    care_id = _create_care_request(client, patient.id)
    res = _create_status(client, patient.id, care_id)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["state"] == "STABLE"
    assert body["severity"] == 4
    assert body["care_request_id"] == care_id
    assert body["patient_id"] == patient.id
    assert body["created_at"]


def test_create_status_update_states(client, patient):
    care_id = _create_care_request(client, patient.id)
    assert _create_status(client, patient.id, care_id, state="IMPROVED").status_code == 201
    assert _create_status(client, patient.id, care_id, state="WORSENED").status_code == 201


def test_unknown_patient_404(client):
    res = _create_status(client, 9999, 1)
    assert res.status_code == 404


def test_unknown_care_request_404(client, patient):
    res = _create_status(client, patient.id, 9999)
    assert res.status_code == 404


def test_care_request_of_other_patient_403(client, patient, other_patient):
    """Regra 3: somente o dono da solicitação pode registrar estado."""
    care_id = _create_care_request(client, patient.id)
    res = _create_status(client, other_patient.id, care_id)
    assert res.status_code == 403


# -- validação de schema (severity / estado) ------------------------------------


@pytest.mark.parametrize("severity", [-1, 11])
def test_severity_out_of_range_422(client, patient, severity):
    care_id = _create_care_request(client, patient.id)
    res = _create_status(client, patient.id, care_id, severity=severity)
    assert res.status_code == 422


def test_severity_limits_ok(client, patient):
    care_id = _create_care_request(client, patient.id)
    assert _create_status(client, patient.id, care_id, severity=0).status_code == 201
    assert _create_status(client, patient.id, care_id, severity=10).status_code == 201


def test_invalid_state_422(client, patient):
    care_id = _create_care_request(client, patient.id)
    res = _create_status(client, patient.id, care_id, state="CURED")
    assert res.status_code == 422


# -- listagens e histórico -------------------------------------------------------


def test_list_by_patient_and_history_order(client, patient):
    care_id = _create_care_request(client, patient.id)
    _create_status(client, patient.id, care_id, state="STABLE", severity=4)
    _create_status(client, patient.id, care_id, state="WORSENED", severity=7)

    res = client.get(f"/api/v1/patient-status/patient/{patient.id}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    # Histórico do paciente: mais recente primeiro (append-only, nada sobrescrito).
    assert items[0]["state"] == "WORSENED"
    assert items[1]["state"] == "STABLE"


def test_list_by_patient_unknown_404(client):
    assert client.get("/api/v1/patient-status/patient/9999").status_code == 404


def test_list_by_patient_invalid_422(client):
    assert client.get("/api/v1/patient-status/patient/0").status_code == 422


def test_list_by_request_unknown_404(client):
    assert client.get("/api/v1/patient-status/request/9999").status_code == 404


def test_get_by_id_404(client):
    assert client.get("/api/v1/patient-status/9999").status_code == 404


def test_get_by_id(client, patient):
    care_id = _create_care_request(client, patient.id)
    created = _create_status(client, patient.id, care_id).json()
    res = client.get(f"/api/v1/patient-status/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


# -- teste de integração ----------------------------------------------------------


def test_integration_user_care_request_status_history(client, patient):
    """User → CareRequest → PatientStatusUpdate → GET histórico."""
    care_id = _create_care_request(client, patient.id)
    s1 = _create_status(client, patient.id, care_id, state="STABLE", severity=4).json()
    s2 = _create_status(client, patient.id, care_id, state="WORSENED", severity=7).json()

    timeline = client.get(f"/api/v1/patient-status/request/{care_id}").json()
    assert [s["id"] for s in timeline] == [s1["id"], s2["id"]]  # ordem cronológica
    assert timeline[0]["state"] == "STABLE" and timeline[0]["severity"] == 4
    assert timeline[1]["state"] == "WORSENED" and timeline[1]["severity"] == 7
    # relatos preservados sem interpretação do sistema
    assert timeline[1]["symptoms"] == "Cansaco"
