"""MED V6 — tests for medical evaluations (comunicação paciente ↔ profissional)."""

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
    user = User(full_name="Maria Paciente", email="maria6@example.com", role="PATIENT")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def doctor(db_session) -> User:
    user = User(full_name="Dr. Joao", email="joao.med6@example.com", role="DOCTOR")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_care_request(client, patient_id: int) -> int:
    res = client.post("/api/v1/care-requests", json={**CARE_REQUEST_PAYLOAD, "patient_id": patient_id})
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _create_status(client, patient_id, care_request_id) -> int:
    res = client.post(
        "/api/v1/patient-status",
        json={
            "patient_id": patient_id,
            "care_request_id": care_request_id,
            "state": "WORSENED",
            "symptoms": "Dor e cansaco",
            "severity": 7,
            "description": "",
            "notes": "",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _create_evaluation(client, professional_id, status_update_id, care_request_id, **overrides):
    payload = {
        "professional_id": professional_id,
        "patient_status_update_id": status_update_id,
        "care_request_id": care_request_id,
        "evaluation": "Informacao recebida e avaliada.",
        "recommendation": "Necessita acompanhamento profissional.",
        **overrides,
    }
    return client.post("/api/v1/medical-evaluations", json=payload)


# -- criação -------------------------------------------------------------------


def test_professional_creates_evaluation(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    res = _create_evaluation(client, doctor.id, status_id, care_id)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["professional_id"] == doctor.id
    assert body["patient_status_update_id"] == status_id
    assert body["care_request_id"] == care_id
    assert body["created_at"]


def test_patient_cannot_create_evaluation(client, patient):
    care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    res = _create_evaluation(client, patient.id, status_id, care_id)
    assert res.status_code == 403


def test_unknown_professional_404(client, patient):
    care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    res = _create_evaluation(client, 9999, status_id, care_id)
    assert res.status_code == 404


def test_unknown_status_update_404(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    res = _create_evaluation(client, doctor.id, 9999, care_id)
    assert res.status_code == 404


def test_unknown_care_request_404(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    res = _create_evaluation(client, doctor.id, status_id, 9999)
    assert res.status_code == 404


def test_status_update_of_other_request_422(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    other_care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    res = _create_evaluation(client, doctor.id, status_id, other_care_id)
    assert res.status_code == 422


# -- listagens e preservação ------------------------------------------------------


def test_list_by_request_and_original_report_preserved(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    original = client.get(f"/api/v1/patient-status/{status_id}").json()

    _create_evaluation(client, doctor.id, status_id, care_id)
    _create_evaluation(client, doctor.id, status_id, care_id, evaluation="Segunda leitura.")

    listing = client.get(f"/api/v1/medical-evaluations/request/{care_id}").json()
    assert len(listing) == 2
    # Relato original permanece intacto (regras 7 e 8).
    after = client.get(f"/api/v1/patient-status/{status_id}").json()
    assert after == original


def test_get_by_id_404(client):
    assert client.get("/api/v1/medical-evaluations/9999").status_code == 404


def test_list_by_request_unknown_404(client):
    assert client.get("/api/v1/medical-evaluations/request/9999").status_code == 404


# -- teste de integração -----------------------------------------------------------


def test_integration_patient_request_status_professional_evaluation(client, patient, doctor):
    """Patient → CareRequest → PatientStatusUpdate → Professional → MedicalEvaluation."""
    care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    created = _create_evaluation(client, doctor.id, status_id, care_id).json()

    detail = client.get(f"/api/v1/medical-evaluations/{created['id']}").json()
    assert detail["professional_id"] == doctor.id
    assert detail["patient_status_update_id"] == status_id

    report = client.get(f"/api/v1/patient-status/request/{care_id}").json()
    assert len(report) == 1 and report[0]["state"] == "WORSENED"
    evals = client.get(f"/api/v1/medical-evaluations/request/{care_id}").json()
    assert len(evals) == 1 and evals[0]["evaluation"] == "Informacao recebida e avaliada."
