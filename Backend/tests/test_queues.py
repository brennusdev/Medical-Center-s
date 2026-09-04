"""MED V4 — tests for queues and prioritization (filas e priorização)."""

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
    user = User(full_name="Maria Paciente", email="maria@example.com", role="PATIENT")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def staff(db_session) -> User:
    user = User(full_name="Ana Recepcao", email="ana@example.com", role="RECEPTIONIST")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_care_request(client, patient, specialty="Cardiologia") -> int:
    res = client.post(
        "/api/v1/care-requests", json={**CARE_REQUEST_PAYLOAD, "specialty": specialty}
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _create_queue(client, care_request_id, specialty="Cardiologia", actor_id=None):
    return client.post(
        "/api/v1/queues",
        json={
            "care_request_id": care_request_id,
            "specialty": specialty,
            "actor_id": actor_id,
        },
    )


# -- criação / posição / prioridade inicial ------------------------------------


def test_create_queue(client, patient):
    care_id = _create_care_request(client, patient)
    res = _create_queue(client, care_id)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["care_request_id"] == care_id
    assert body["specialty"] == "Cardiologia"
    assert body["status"] == "WAITING"
    assert body["priority"] == "NORMAL"
    assert body["position"] == 1
    assert body["entered_at"] and body["updated_at"]


def test_create_queue_care_request_not_found(client):
    res = _create_queue(client, 9999)
    assert res.status_code == 404
    assert "não encontrada" in res.json()["detail"]


def test_duplicate_active_queue_same_specialty(client, patient):
    care_id = _create_care_request(client, patient)
    assert _create_queue(client, care_id).status_code == 201
    res = _create_queue(client, care_id)
    assert res.status_code == 422
    assert "entrada ativa" in res.json()["detail"]


def test_initial_position_increments(client, patient):
    """Posições iniciais: fim da fila (1, 2, 3...)."""
    care1 = _create_care_request(client, patient, "Dermatologia")
    care2 = _create_care_request(client, patient, "Dermatologia")
    care3 = _create_care_request(client, patient, "Dermatologia")
    r1 = _create_queue(client, care1, "Dermatologia").json()
    r2 = _create_queue(client, care2, "Dermatologia").json()
    r3 = _create_queue(client, care3, "Dermatologia").json()
    assert (r1["position"], r2["position"], r3["position"]) == (1, 2, 3)


# -- histórico (QueueEvent) ----------------------------------------------------


def test_created_event_generated(client, patient):
    care_id = _create_care_request(client, patient)
    queue = _create_queue(client, care_id).json()
    res = client.get(f"/api/v1/queues/{queue['id']}/events")
    assert res.status_code == 200
    events = res.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "CREATED"
    assert events[0]["new_position"] == 1
    assert events[0]["new_priority"] == "NORMAL"


def test_events_endpoint_404(client):
    assert client.get("/api/v1/queues/9999/events").status_code == 404


# -- alteração de prioridade ---------------------------------------------------


def test_update_priority_and_events(client, patient, staff):
    care_id = _create_care_request(client, patient)
    queue = _create_queue(client, care_id).json()

    res = client.patch(
        f"/api/v1/queues/{queue['id']}/priority",
        json={"priority": "HIGH", "actor_id": staff.id},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["priority"] == "HIGH"

    events = client.get(f"/api/v1/queues/{queue['id']}/events").json()
    types = [e["event_type"] for e in events]
    assert "PRIORITY_CHANGED" in types
    priority_event = next(e for e in events if e["event_type"] == "PRIORITY_CHANGED")
    assert priority_event["previous_priority"] == "NORMAL"
    assert priority_event["new_priority"] == "HIGH"
    assert priority_event["actor_id"] == staff.id  # regra 14: mudança associada ao responsável


def test_priority_change_same_value_no_event(client, patient, staff):
    care_id = _create_care_request(client, patient)
    queue = _create_queue(client, care_id).json()
    res = client.patch(
        f"/api/v1/queues/{queue['id']}/priority",
        json={"priority": "NORMAL", "actor_id": staff.id},
    )
    assert res.status_code == 200
    events = client.get(f"/api/v1/queues/{queue['id']}/events").json()
    assert [e["event_type"] for e in events] == ["CREATED"]  # sem PRIORITY_CHANGED


def test_patient_cannot_change_priority(client, patient, staff):
    """Regra 13: paciente não pode alterar a própria prioridade (403)."""
    care_id = _create_care_request(client, patient)
    queue = _create_queue(client, care_id).json()
    res = client.patch(
        f"/api/v1/queues/{queue['id']}/priority",
        json={"priority": "URGENT", "actor_id": patient.id},
    )
    assert res.status_code == 403
    assert "Pacientes não podem" in res.json()["detail"]
    # prioridade permanece NORMAL
    assert client.get(f"/api/v1/queues/{queue['id']}").json()["priority"] == "NORMAL"


def test_unknown_actor_404(client, patient):
    care_id = _create_care_request(client, patient)
    queue = _create_queue(client, care_id).json()
    res = client.patch(
        f"/api/v1/queues/{queue['id']}/priority",
        json={"priority": "HIGH", "actor_id": 9999},
    )
    assert res.status_code == 404


def test_unauthorized_role_403(client, patient, db_session):
    """Somente usuários autorizados no domínio alteram prioridade (regra 12)."""
    other = User(full_name="Externo", email="ext@example.com", role="OTHER")
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    care_id = _create_care_request(client, patient)
    queue = _create_queue(client, care_id).json()
    res = client.patch(
        f"/api/v1/queues/{queue['id']}/priority",
        json={"priority": "HIGH", "actor_id": other.id},
    )
    assert res.status_code == 403


# -- reorganização determinística ----------------------------------------------


def _seed_queue(client, patient, specialty="Cardiologia"):
    care_id = _create_care_request(client, patient, specialty)
    return _create_queue(client, care_id, specialty).json()


def test_reorganization_order_and_position_events(client, patient, staff):
    """URGENT > HIGH > MEDIUM > NORMAL; empate: menor entered_at primeiro."""
    q1 = _seed_queue(client, patient)
    q2 = _seed_queue(client, patient)
    q3 = _seed_queue(client, patient)
    q4 = _seed_queue(client, patient)
    assert [q["position"] for q in (q1, q2, q3, q4)] == [1, 2, 3, 4]

    # Promove o último (q4) a URGENT: deve ir para a posição 1.
    res = client.patch(
        f"/api/v1/queues/{q4['id']}/priority",
        json={"priority": "URGENT", "actor_id": staff.id},
    )
    assert res.status_code == 200, res.text

    queues = client.get(f"/api/v1/queues/patient/{patient.id}").json()
    by_id = {q["id"]: q["position"] for q in queues}
    assert by_id[q4["id"]] == 1
    assert by_id[q1["id"]] == 2
    assert by_id[q2["id"]] == 3
    assert by_id[q3["id"]] == 4

    # POSITION_CHANGED gerado para cada item movido (inclusive quem perdeu posição).
    events_q1 = client.get(f"/api/v1/queues/{q1['id']}/events").json()
    moves_q1 = [e for e in events_q1 if e["event_type"] == "POSITION_CHANGED"]
    assert len(moves_q1) == 1
    assert moves_q1[0]["previous_position"] == 1
    assert moves_q1[0]["new_position"] == 2

    events_q4 = client.get(f"/api/v1/queues/{q4['id']}/events").json()
    moves_q4 = [e for e in events_q4 if e["event_type"] == "POSITION_CHANGED"]
    assert len(moves_q4) == 1
    assert (moves_q4[0]["previous_position"], moves_q4[0]["new_position"]) == (4, 1)
    assert moves_q4[0]["actor_id"] == staff.id

    # Eventos de PRIORITY_CHANGED e POSITION_CHANGED são distintos.
    assert any(e["event_type"] == "PRIORITY_CHANGED" for e in events_q4)


def test_reorganization_tie_by_entered_at(client, patient, staff):
    """Mesma prioridade: menor entered_at primeiro (sem trocas indevidas)."""
    q1 = _seed_queue(client, patient)
    q2 = _seed_queue(client, patient)
    q3 = _seed_queue(client, patient)

    # Promove q3 a HIGH — q3 vai para a 1; os demais mantêm a ordem de entrada.
    res = client.patch(
        f"/api/v1/queues/{q3['id']}/priority",
        json={"priority": "HIGH", "actor_id": staff.id},
    )
    assert res.status_code == 200
    queues = client.get(f"/api/v1/queues/patient/{patient.id}").json()
    by_id = {q["id"]: q["position"] for q in queues}
    assert (by_id[q3["id"]], by_id[q1["id"]], by_id[q2["id"]]) == (1, 2, 3)


def test_removed_entry_stays_in_history(client, patient, staff, db_session):
    """Histórico não é apagado: eventos continuam listados após mudanças."""
    q1 = _seed_queue(client, patient)
    q2 = _seed_queue(client, patient)

    client.patch(
        f"/api/v1/queues/{q2['id']}/priority",
        json={"priority": "MEDIUM", "actor_id": staff.id},
    )
    events = client.get(f"/api/v1/queues/{q1['id']}/events").json()
    assert len(events) >= 1  # CREATED permanece (imutável)
    assert any(e["event_type"] == "POSITION_CHANGED" for e in events)


# -- listagem da fila do paciente -----------------------------------------------


def test_list_by_patient(client, patient, db_session):
    care_cardio = _create_care_request(client, patient, "Cardiologia")
    care_derm = _create_care_request(client, patient, "Dermatologia")
    _create_queue(client, care_cardio, "Cardiologia")
    _create_queue(client, care_derm, "Dermatologia")

    res = client.get(f"/api/v1/queues/patient/{patient.id}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    assert {i["specialty"] for i in items} == {"Cardiologia", "Dermatologia"}

    # paciente sem filas → lista vazia
    assert client.get("/api/v1/queues/patient/4242").json() == []

    # patient_id inválido
    assert client.get("/api/v1/queues/patient/0").status_code == 422


def test_get_queue_by_id_404(client):
    assert client.get("/api/v1/queues/9999").status_code == 404
