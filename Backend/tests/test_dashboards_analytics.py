"""MED V8 — Testes de Dashboards e Analytics.

Cobertura:
- dashboards por perfil (paciente, médico, hospital, admin);
- casos vazios (nenhum atendimento/consulta/fila/hospital sem solicitações);
- filtros de período, especialidade e hospital;
- contagens, agrupamentos e tempo médio (agregação SQL).
"""

from datetime import datetime, timedelta, timezone

from App.modules.appointments.models import Appointment, AppointmentStatus
from App.modules.appointments.schemas import AppointmentCreate, AppointmentRequestCreate
from App.modules.appointments.service import AppointmentService
from App.modules.care_requests.models import CareRequest
from App.modules.care_requests.schemas import CareRequestCreate
from App.modules.care_requests.service import CareRequestService
from App.modules.queues.schemas import QueueCreate
from App.modules.queues.service import QueueService
from App.modules.users.models import User


def _mk_user(db, full_name="Ana Clara", role="PATIENT") -> User:
    u = User(full_name=full_name, email=f"{full_name.replace(' ', '.').lower()}@ex.com", role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _mk_care_request(db, patient_id: int, specialty="Cardiologia") -> CareRequest:
    return CareRequestService(db).create(
        CareRequestCreate(
            patient_id=patient_id,
            reason="Dor no peito",
            specialty=specialty,
            symptoms="dor",
            description="desc",
            cep="01310100",
            referral="",
            discomfort_level=5,
            symptom_onset="2026-01-01",
            notes="",
        )
    )


def _mk_queue(db, care_request_id: int, specialty="Cardiologia", hospital_id=10):
    return QueueService(db).create(
        QueueCreate(care_request_id=care_request_id, specialty=specialty, hospital_id=hospital_id, actor_id=None)
    )


def _mk_appointment(db, patient_id: int, when: datetime):
    svc = AppointmentService(db)
    req = svc.create_request(
        AppointmentRequestCreate(
            patient_id=patient_id,
            specialty="Cardiologia",
            preferred_date=when.date().isoformat(),
            preferred_time=when.strftime("%H:%M"),
            reason="rotina",
        )
    )
    return svc.create_appointment(AppointmentCreate(request_id=req.id, doctor_name="Dr. Joao", hospital_name="Hospital X", scheduled_at=when, notes=""))


# ---------------------------------------------------------------------------
# Dashboard do paciente
# ---------------------------------------------------------------------------

def test_patient_dashboard_empty(client, db_session):
    u = _mk_user(db_session)
    res = client.get(f"/api/v1/dashboard/patient/{u.id}")
    assert res.status_code == 200
    body = res.json()
    assert body["next_appointment"] is None
    assert body["open_care_requests"] == []
    assert body["queues"] == []
    assert body["unread_notifications"] == 0


def test_patient_dashboard_full_flow(client, db_session):
    u = _mk_user(db_session)
    cr = _mk_care_request(db_session, u.id)
    _mk_queue(db_session, cr.id)
    _mk_appointment(db_session, u.id, datetime.now(timezone.utc) + timedelta(days=7))
    res = client.get(f"/api/v1/dashboard/patient/{u.id}")
    assert res.status_code == 200
    body = res.json()
    assert body["next_appointment"]["specialty"] == "Cardiologia"
    assert body["next_step"] == "Você possui consulta agendada."
    assert len(body["open_care_requests"]) == 1
    assert body["queues"][0]["position"] == 1
    assert body["queues"][0]["priority"] == "NORMAL"


def test_patient_dashboard_404(client):
    assert client.get("/api/v1/dashboard/patient/9999").status_code == 404


# ---------------------------------------------------------------------------
# Dashboard do médico / hospital / admin
# ---------------------------------------------------------------------------

def test_doctor_dashboard_lists_cases(client, db_session):
    doc = _mk_user(db_session, "Dr. Joao", role="DOCTOR")
    p = _mk_user(db_session, "Bruno", role="PATIENT")
    cr = _mk_care_request(db_session, p.id)
    _mk_queue(db_session, cr.id)
    res = client.get(f"/api/v1/dashboard/doctor/{doc.id}")
    assert res.status_code == 200
    body = res.json()
    assert any(c["id"] == cr.id for c in body["received_requests"])
    assert body["active_queues"]


def test_hospital_dashboard_groups_by_specialty(client, db_session):
    p = _mk_user(db_session, "Carla")
    cr1 = _mk_care_request(db_session, p.id, "Cardiologia")
    cr2 = _mk_care_request(db_session, p.id, "Ortopedia")
    _mk_queue(db_session, cr1.id, "Cardiologia", hospital_id=10)
    _mk_queue(db_session, cr2.id, "Ortopedia", hospital_id=10)
    res = client.get("/api/v1/dashboard/hospital/10")
    assert res.status_code == 200
    body = res.json()
    assert body["open_queues_count"] == 2
    specialties = {e["specialty"] for e in body["by_specialty"]}
    assert specialties == {"Cardiologia", "Ortopedia"}


def test_hospital_without_requests_empty(client):
    res = client.get("/api/v1/dashboard/hospital/42")
    assert res.status_code == 200
    assert res.json()["open_queues"] == []


def test_admin_dashboard_aggregates(client, db_session):
    p = _mk_user(db_session, "Duda")
    cr = _mk_care_request(db_session, p.id)
    _mk_queue(db_session, cr.id)
    res = client.get("/api/v1/dashboard/admin")
    assert res.status_code == 200
    body = res.json()
    assert body["total_care_requests"] == 1
    assert body["open_care_requests"] == 1
    assert body["waiting_queue_entries"] == 1
    assert any(e["key"] == "Cardiologia" for e in body["by_specialty"])


# ---------------------------------------------------------------------------
# Analytics: contagem, agrupamento, tempo médio e filtros
# ---------------------------------------------------------------------------

def test_analytics_overview_counts(client, db_session):
    p = _mk_user(db_session, "Elisa")
    cr = _mk_care_request(db_session, p.id)
    _mk_queue(db_session, cr.id)
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 200
    body = res.json()
    assert body["total_care_requests"] >= 1
    assert body["open_care_requests"] >= 1
    assert body["waiting_queue_entries"] >= 1


def test_analytics_specialties_grouping(client, db_session):
    p = _mk_user(db_session, "Felipe")
    _mk_care_request(db_session, p.id, "Dermatologia")
    _mk_care_request(db_session, p.id, "Dermatologia")
    res = client.get("/api/v1/analytics/specialties")
    assert res.status_code == 200
    derm = next(e for e in res.json() if e["key"] == "Dermatologia")
    assert derm["total"] == 2
    assert derm["open"] == 2


def test_analytics_specialty_filter(client, db_session):
    p = _mk_user(db_session, "Gustavo")
    _mk_care_request(db_session, p.id, "Cardiologia")
    _mk_care_request(db_session, p.id, "Ortopedia")
    res = client.get("/api/v1/analytics/specialties", params={"specialty": "Ortopedia"})
    keys = {e["key"] for e in res.json()}
    assert keys == {"Ortopedia"}


def test_analytics_invalid_period_422(client):
    res = client.get(
        "/api/v1/analytics/overview",
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert res.status_code == 422


def test_analytics_period_filter_empty(client, db_session):
    p = _mk_user(db_session, "Helena")
    _mk_care_request(db_session, p.id)
    # Janela passada (antes de qualquer registro) → listas vazias, sem erro.
    res = client.get(
        "/api/v1/analytics/specialties",
        params={"start_date": "2020-01-01", "end_date": "2020-01-31"},
    )
    assert res.status_code == 200
    assert res.json() == []


def test_analytics_wait_times_empty(client):
    res = client.get("/api/v1/analytics/wait-times")
    assert res.status_code == 200
    body = res.json()
    assert body["average_wait_hours"] is None
    assert body["samples"] == 0


def test_analytics_hospitals_grouping(client, db_session):
    p = _mk_user(db_session, "Ivo")
    cr = _mk_care_request(db_session, p.id)
    _mk_queue(db_session, cr.id, hospital_id=10)
    res = client.get("/api/v1/analytics/hospitals")
    keys = {e["key"] for e in res.json()}
    assert "HOSPITAL 10" in keys


def test_analytics_priorities(client, db_session):
    p = _mk_user(db_session, "Júlia")
    cr = _mk_care_request(db_session, p.id)
    _mk_queue(db_session, cr.id)
    res = client.get("/api/v1/analytics/priorities")
    body = res.json()
    assert any(e["priority"] == "NORMAL" for e in body)


def test_analytics_appointments_by_period(client, db_session):
    p = _mk_user(db_session, "Kaio")
    _mk_appointment(db_session, p.id, datetime.now(timezone.utc) + timedelta(days=3))
    res = client.get("/api/v1/analytics/appointments")
    assert res.status_code == 200
    assert res.json()
