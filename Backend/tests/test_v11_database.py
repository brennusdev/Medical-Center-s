"""MED V11 — Testes de banco avançado.

Cobre: constraints (check/unique), paginação, database health e regressão
dos fluxos V1–V10 (a suíte inteira é a regressão; aqui os pontos novos).
"""

import pytest
from sqlalchemy.exc import IntegrityError

from App.core.health import check_database
from App.modules.care_requests.models import CareRequest
from App.modules.notifications.repository import NotificationRepository
from App.modules.notifications.service import NotificationService
from App.modules.queues.models import Queue, QueueEvent, QueueEventType
from App.modules.queues.repository import QueueRepository
from App.modules.users.models import User


@pytest.fixture
def user(db_session) -> User:
    u = User(full_name="Paciente V11", email="v11@med.local", role="PATIENT")
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def care_request(db_session, user) -> CareRequest:
    from datetime import date

    cr = CareRequest(
        patient_id=user.id,
        reason="Dor nas costas há uma semana",
        specialty="Ortopedia",
        symptoms="dor lombar",
        description="dor ao levantar",
        cep="01001000",
        referral="",
        discomfort_level=5,
        symptom_onset=date(2026, 2, 1),
        notes="",
    )
    db_session.add(cr)
    db_session.commit()
    db_session.refresh(cr)
    return cr


# -- Constraints ------------------------------------------------------------

def test_check_constraint_severity_range(db_session, user, care_request):
    """severity fora de 0..10 deve ser rejeitada PELO BANCO (não só pelo Pydantic)."""
    from App.modules.patient_status.models import PatientState, PatientStatusUpdate

    update = PatientStatusUpdate(
        patient_id=user.id,
        care_request_id=care_request.id,
        state=PatientState.STABLE,
        severity=11,  # fora da faixa
    )
    db_session.add(update)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_constraint_queue_position_positive(db_session, care_request):
    """position 0 viola a constraint estrutural da fila."""
    queue = Queue(care_request_id=care_request.id, specialty="Ortopedia", position=0)
    db_session.add(queue)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_user_email(db_session, user):
    duplicate = User(full_name="Duplicado", email=user.email, role="PATIENT")
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# -- Paginação (V11) ----------------------------------------------------------

def test_notifications_paged(db_session, user):
    svc = NotificationService(db_session)
    for i in range(7):
        svc.emit(
            user_id=user.id,
            type_="CARE_REQUEST_RECEIVED",
            title=f"Notificação {i}",
            message="mensagem",
        )
    repo = NotificationRepository(db_session)
    page1, total = repo.list_by_user_paged(user.id, limit=3, offset=0)
    page2, _ = repo.list_by_user_paged(user.id, limit=3, offset=3)
    assert total == 7
    assert len(page1) == 3
    assert len(page2) == 3
    # Sem sobreposição entre páginas.
    ids1 = {n.id for n in page1}
    ids2 = {n.id for n in page2}
    assert not (ids1 & ids2)
    # Mais recente primeiro.
    assert page1[0].created_at >= page1[-1].created_at


def test_queue_events_paged(db_session, user, care_request):
    repo = QueueRepository(db_session)
    queue = repo.create(Queue(care_request_id=care_request.id, specialty="Ortopedia", position=1))
    for i in range(5):
        repo.add_event(
            QueueEvent(queue_id=queue.id, event_type=QueueEventType.STATUS_CHANGED, description=f"e{i}")
        )
    page, total = repo.list_events_paged(queue.id, limit=2, offset=0)
    assert total == 5  # 4 eventos + CREATED
    assert len(page) == 2
    # Ordenação cronológica.
    assert page[0].created_at <= page[1].created_at


# -- Database health (V11) ----------------------------------------------------

def test_database_health_ok(db_session):
    result = check_database(db_session)
    assert result["ok"] is True
    assert result["latency_ms"] is not None


def test_database_health_no_credentials_leak(db_session):
    """Contrato de segurança: payload nunca contém conexão/credenciais."""
    result = check_database(db_session)
    assert set(result.keys()) == {"ok", "latency_ms"}


# -- Regressão de integridade V1–V10 (conjunto mínimo) ------------------------

def test_regression_queue_ordering_after_priority(db_session, user, care_request):
    """A constraint nova não alterou o comportamento da fila (V4 preservada)."""
    from App.modules.queues.models import QueuePriority
    from App.modules.queues.service import QueueService

    svc = QueueService(db_session)
    from App.modules.queues.models import QueuePriority
    from App.modules.queues.service import QueueService

    q1 = svc.create(type("D", (), {"care_request_id": care_request.id, "specialty": "Ortopedia",
                                  "hospital_id": None, "actor_id": None})())
    # q2 entra na fila só para a reorganização ter com quem competir (sem asserts próprios).
    svc.create(type("D", (), {"care_request_id": care_request.id, "specialty": "Cardiologia",
                                   "hospital_id": None, "actor_id": None})())
    doctor = User(full_name="Dr", email="dr11@med.local", role="DOCTOR")
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    svc.update_priority(q1.id, QueuePriority.URGENT, doctor.id)
    assert q1.position == 1
