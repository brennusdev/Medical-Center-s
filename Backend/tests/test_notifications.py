"""MED V7 — tests for notifications."""

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
    user = User(full_name="Maria Paciente", email="maria7@example.com", role="PATIENT")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def doctor(db_session) -> User:
    user = User(full_name="Dr. Ana", email="ana.med7@example.com", role="DOCTOR")
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


def _create_queue(client, care_request_id, actor_id) -> int:
    res = client.post(
        "/api/v1/queues",
        json={"care_request_id": care_request_id, "specialty": "Cardiologia", "actor_id": actor_id},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


# -- criação / listagem / histórico ------------------------------------------------


def test_create_notification_via_care_request_event(client, patient):
    care_id = _create_care_request(client, patient.id)
    res = client.get(f"/api/v1/notifications/user/{patient.id}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["type"] == "CARE_REQUEST_RECEIVED"
    assert items[0]["title"] == "Solicitação recebida"
    assert items[0]["read"] is False
    assert items[0]["related_resource_type"] == "care_request"
    assert items[0]["related_resource_id"] == care_id
    assert items[0]["created_at"]


def test_list_empty_and_invalid(client, patient):
    assert client.get(f"/api/v1/notifications/user/{patient.id}").json() == []
    assert client.get("/api/v1/notifications/user/0").status_code == 422


def test_correct_user_sees_own_notifications(client, patient, doctor):
    _create_care_request(client, patient.id)
    # Outro usuário não vê as notificações do paciente na listagem dele.
    assert client.get(f"/api/v1/notifications/user/{doctor.id}").json() == []


def test_get_notification_wrong_user_403(client, patient, doctor):
    _create_care_request(client, patient.id)
    items = client.get(f"/api/v1/notifications/user/{patient.id}").json()
    nid = items[0]["id"]
    assert client.get(f"/api/v1/notifications/{nid}?user_id={patient.id}").status_code == 200
    res = client.get(f"/api/v1/notifications/{nid}?user_id={doctor.id}")
    assert res.status_code == 403


def test_get_notification_unknown_404(client, patient):
    assert client.get(f"/api/v1/notifications/9999?user_id={patient.id}").status_code == 404


def test_mark_read_preserves_notification(client, patient):
    _create_care_request(client, patient.id)
    nid = client.get(f"/api/v1/notifications/user/{patient.id}").json()[0]["id"]
    res = client.patch(f"/api/v1/notifications/{nid}/read?user_id={patient.id}")
    assert res.status_code == 200
    assert res.json()["read"] is True
    # Regra 6: marcar como lida não apaga; histórico permanece.
    items = client.get(f"/api/v1/notifications/user/{patient.id}").json()
    assert len(items) == 1 and items[0]["read"] is True


def test_mark_read_wrong_user_403(client, patient, doctor):
    _create_care_request(client, patient.id)
    nid = client.get(f"/api/v1/notifications/user/{patient.id}").json()[0]["id"]
    assert client.patch(f"/api/v1/notifications/{nid}/read?user_id={doctor.id}").status_code == 403


# -- notificações por evento de domínio ---------------------------------------------


def test_queue_position_notification(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    _create_queue(client, care_request_id=care_id, actor_id=doctor.id)
    types = [n["type"] for n in client.get(f"/api/v1/notifications/user/{patient.id}").json()]
    assert "QUEUE_POSITION_CHANGED" in types


def test_queue_priority_notification(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    queue_id = _create_queue(client, care_request_id=care_id, actor_id=doctor.id)
    res = client.patch(f"/api/v1/queues/{queue_id}/priority", json={"priority": "HIGH", "actor_id": doctor.id})
    assert res.status_code == 200, res.text
    types = [n["type"] for n in client.get(f"/api/v1/notifications/user/{patient.id}").json()]
    assert "QUEUE_PRIORITY_CHANGED" in types


def test_patient_status_notification_to_professional_context(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    _create_status(client, patient.id, care_id)
    types = [n["type"] for n in client.get(f"/api/v1/notifications/user/{doctor.id}").json()]
    assert "PATIENT_STATUS_UPDATED" in types


def test_medical_evaluation_notification_to_patient(client, patient, doctor):
    care_id = _create_care_request(client, patient.id)
    status_id = _create_status(client, patient.id, care_id)
    res = client.post(
        "/api/v1/medical-evaluations",
        json={
            "professional_id": doctor.id,
            "patient_status_update_id": status_id,
            "care_request_id": care_id,
            "evaluation": "Informacao recebida e avaliada.",
            "recommendation": "",
        },
    )
    assert res.status_code == 201, res.text
    types = [n["type"] for n in client.get(f"/api/v1/notifications/user/{patient.id}").json()]
    assert "MEDICAL_EVALUATION_CREATED" in types


def test_appointment_scheduled_notification(client, patient, doctor):
    # Prepara appointment_request via API (V2).
    res = client.post(
        "/api/v1/appointments/requests",
        json={
            "patient_id": patient.id,
            "specialty": "Cardiologia",
            "preferred_date": "2030-06-01",
            "preferred_time": "10:00",
            "reason": "Checkup",
        },
    )
    assert res.status_code == 201, res.text
    request_id = res.json()["id"]
    res = client.post(
        "/api/v1/appointments",
        json={
            "request_id": request_id,
            "doctor_name": "Dr. Ana",
            "hospital_name": "Hospital Central",
            "scheduled_at": "2030-06-01T10:00:00+00:00",
            "notes": "",
        },
    )
    assert res.status_code == 201, res.text
    types = [n["type"] for n in client.get(f"/api/v1/notifications/user/{patient.id}").json()]
    assert "APPOINTMENT_SCHEDULED" in types


# -- teste de integração ------------------------------------------------------------


def test_integration_status_update_to_notification_listing(client, patient, doctor):
    """PatientStatusUpdate → NotificationService → Notification → GET notifications."""
    care_id = _create_care_request(client, patient.id)
    _create_status(client, patient.id, care_id)

    items = client.get(f"/api/v1/notifications/user/{doctor.id}").json()
    assert any(n["type"] == "PATIENT_STATUS_UPDATED" and n["read"] is False for n in items)
    nid = next(n["id"] for n in items if n["type"] == "PATIENT_STATUS_UPDATED")
    assert client.patch(f"/api/v1/notifications/{nid}/read?user_id={doctor.id}").status_code == 200
