﻿"""MED V2 tests â€” appointments and scheduling."""

from datetime import datetime, timezone

import pytest

API = "/api/v1/appointments"


def make_request(client, patient_id=1, specialty="Cardiologia", date="2030-05-20", time="09:00", reason="Dor no peito"):
    payload = {
        "patient_id": patient_id,
        "specialty": specialty,
        "preferred_date": date,
        "preferred_time": time,
        "reason": reason,
    }
    resp = client.post(f"{API}/requests", json=payload)
    return resp


# -- 1. CriaÃ§Ã£o de solicitaÃ§Ã£o ------------------------------------------------
def test_create_request_success(client):
    resp = make_request(client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["patient_id"] == 1
    assert body["specialty"] == "Cardiologia"
    assert body["preferred_date"] == "2030-05-20"
    assert body["preferred_time"] == "09:00:00"
    assert body["status"] == "REQUESTED"
    assert body["created_at"]


def test_list_requests_by_patient(client):
    make_request(client, patient_id=7)
    make_request(client, patient_id=7, specialty="Dermatologia")
    make_request(client, patient_id=8)

    resp = client.get(f"{API}/requests/patient/7")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert all(i["patient_id"] == 7 for i in items)


# -- 2. ValidaÃ§Ã£o dos dados ---------------------------------------------------
@pytest.mark.parametrize(
    "payload",
    [
        {"patient_id": 0, "specialty": "Cardiologia", "preferred_date": "2030-05-20", "preferred_time": "09:00"},
        {"patient_id": -1, "specialty": "Cardiologia", "preferred_date": "2030-05-20", "preferred_time": "09:00"},
        {"patient_id": 1, "specialty": "", "preferred_date": "2030-05-20", "preferred_time": "09:00"},
        {"patient_id": 1, "specialty": "Cardiologia", "preferred_date": "not-a-date", "preferred_time": "09:00"},
        {"patient_id": 1, "specialty": "Cardiologia", "preferred_date": "2030-05-20", "preferred_time": "25:00"},
    ],
)
def test_create_request_invalid_data(client, payload):
    resp = client.post(f"{API}/requests", json=payload)
    assert resp.status_code == 422


# -- 3. CriaÃ§Ã£o de consulta ---------------------------------------------------
def test_create_appointment_success(client, future_datetime):
    request = make_request(client).json()
    resp = client.post(
        API,
        json={
            "request_id": request["id"],
            "doctor_name": "Dra. Ana Souza",
            "hospital_name": "Hospital Central",
            "scheduled_at": future_datetime,
            "notes": "Levar exames anteriores",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["request_id"] == request["id"]
    assert body["patient_id"] == request["patient_id"]
    assert body["specialty"] == "Cardiologia"
    assert body["doctor_name"] == "Dra. Ana Souza"
    assert body["status"] == "SCHEDULED"


def test_create_appointment_updates_request_status(client, future_datetime):
    request = make_request(client).json()
    client.post(API, json={"request_id": request["id"], "doctor_name": "Dr. X", "hospital_name": "HC", "scheduled_at": future_datetime})
    detail = client.get(f"{API}/requests/patient/{request['patient_id']}").json()[0]
    assert detail["status"] == "SCHEDULED"


# -- 4. ValidaÃ§Ã£o de paciente --------------------------------------------------
def test_create_appointment_with_unknown_request(client, future_datetime):
    resp = client.post(
        API,
        json={"request_id": 9999, "doctor_name": "Dr. X", "hospital_name": "HC", "scheduled_at": future_datetime},
    )
    assert resp.status_code == 404


def test_invalid_patient_id_rejected(client):
    resp = client.get(f"{API}/patient/0")
    assert resp.status_code == 422
    resp = client.get(f"{API}/requests/patient/-3")
    assert resp.status_code == 422


# -- 5. Consulta futura --------------------------------------------------------
def test_appointment_must_be_in_future(client):
    request = make_request(client).json()
    past = "2020-01-01T10:00:00+00:00"
    resp = client.post(
        API,
        json={"request_id": request["id"], "doctor_name": "Dr. X", "hospital_name": "HC", "scheduled_at": past},
    )
    assert resp.status_code == 422
    assert "futura" in resp.json()["detail"]


def test_next_appointment_returns_earliest_future(client, db_session):
    from App.core.main import app  # noqa: F401
    from App.modules.appointments.service import AppointmentService
    from App.modules.appointments.schemas import AppointmentRequestCreate

    service = AppointmentService(db_session, now=datetime(2030, 1, 1, 8, 0, tzinfo=timezone.utc))
    req1 = service.create_request(
        AppointmentRequestCreate(patient_id=5, specialty="Ortopedia", preferred_date="2031-06-01", preferred_time="09:00")
    )
    req2 = service.create_request(
        AppointmentRequestCreate(patient_id=5, specialty="Ortopedia", preferred_date="2031-06-01", preferred_time="14:00")
    )
    from App.modules.appointments.schemas import AppointmentCreate

    service.create_appointment(
        AppointmentCreate(request_id=req1.id, doctor_name="Dr. A", hospital_name="H1", scheduled_at=datetime(2031, 6, 10, 9, 0, tzinfo=timezone.utc))
    )
    service.create_appointment(
        AppointmentCreate(request_id=req2.id, doctor_name="Dr. B", hospital_name="H2", scheduled_at=datetime(2031, 6, 5, 9, 0, tzinfo=timezone.utc))
    )
    nxt = service.next_appointment(5)
    assert nxt is not None
    assert nxt.doctor_name == "Dr. B"  # earliest future one


# -- 6. Relacionamento solicitaÃ§Ã£o <-> consulta ---------------------------------
def test_request_and_appointment_relationship(client, db_session, future_datetime):
    request = make_request(client).json()
    appt = client.post(
        API,
        json={"request_id": request["id"], "doctor_name": "Dr. X", "hospital_name": "HC", "scheduled_at": future_datetime},
    ).json()
    assert appt["request_id"] == request["id"]

    from App.modules.appointments.repository import AppointmentRepository

    repo = AppointmentRepository(db_session)
    stored = repo.get(appt["id"])
    assert stored.request.id == request["id"]
    assert stored.request.appointments[0].id == appt["id"]


def test_get_appointment_not_found(client):
    resp = client.get(f"{API}/9999")
    assert resp.status_code == 404


