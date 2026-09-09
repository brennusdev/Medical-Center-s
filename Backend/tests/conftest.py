"""Test fixtures for MED V2 appointments."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from App.core.database import Base, get_db
from App.core.main import app
from App.core.models import Base as _registry  # noqa: F401 â€” ensures models are registered

TEST_DB_URL = "sqlite://"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 1, 1, 8, 0, tzinfo=UTC)


@pytest.fixture
def future_datetime() -> str:
    return "2030-06-01T10:00:00+00:00"


# ---------------------------------------------------------------------------
# MED V13 — Fixtures compartilhadas de usuários e fábricas de dados.
# Centralizar aqui evita que cada arquivo de teste reimplemente `_mk_user`/
# `_mk_care_request` com pequenas divergências (fonte clássica de falso-negativo).
# ---------------------------------------------------------------------------

from App.modules.care_requests.models import CareRequest  # noqa: E402
from App.modules.queues.models import Queue  # noqa: E402
from App.modules.users.models import User  # noqa: E402


@pytest.fixture
def make_user(db_session):
    """Fábrica de usuários: `make_user(role="DOCTOR")`."""
    counter = {"n": 0}

    def _make(role: str = "PATIENT", full_name: str | None = None, email: str | None = None) -> User:
        counter["n"] += 1
        u = User(
            full_name=full_name or f"Usuário {counter['n']}",
            email=email or f"user{counter['n']}@med.local",
            role=role,
        )
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        return u

    return _make


@pytest.fixture
def patient(make_user) -> User:
    return make_user("PATIENT", "Paciente Teste")


@pytest.fixture
def doctor(make_user) -> User:
    return make_user("DOCTOR", "Doutor Teste")


@pytest.fixture
def admin(make_user) -> User:
    return make_user("ADMIN", "Admin Teste")


@pytest.fixture
def make_care_request(db_session):
    """Fábrica de CareRequest (modelo direto — sem passar por HTTP)."""
    from datetime import date

    counter = {"n": 0}

    def _make(patient_id: int, specialty: str = "Clínica Geral") -> CareRequest:
        counter["n"] += 1
        cr = CareRequest(
            patient_id=patient_id,
            reason=f"Motivo {counter['n']}",
            specialty=specialty,
            symptoms="sintomas",
            description="descrição",
            cep="01001000",
            referral="",
            discomfort_level=5,
            symptom_onset=date(2026, 1, 1),
            notes="",
        )
        db_session.add(cr)
        db_session.commit()
        db_session.refresh(cr)
        return cr

    return _make


@pytest.fixture
def make_queue(db_session):
    """Fábrica de entradas de fila (position no fim da fila da especialidade)."""

    def _make(care_request_id: int, specialty: str = "Clínica Geral", position: int | None = None) -> Queue:
        if position is None:
            last = (
                db_session.query(Queue)
                .filter(Queue.specialty == specialty)
                .order_by(Queue.position.desc())
                .first()
            )
            position = (last.position + 1) if last else 1
        q = Queue(care_request_id=care_request_id, specialty=specialty, position=position)
        db_session.add(q)
        db_session.commit()
        db_session.refresh(q)
        return q

    return _make

