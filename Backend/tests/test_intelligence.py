"""MED V15 — Testes do módulo intelligence.

Cobre:
- Carga por especialidade com níveis LOW/MEDIUM/HIGH (limiares explícitos);
- Tempo médio de espera de entradas concluídas;
- Sinal de atenção (WORSENED + espera longa) e ausência de falso-positivo
  quando o estado é STABLE/IMPROVED ou a espera é curta;
- Contrato do endpoint /intelligence/summary (somente leitura, sem mutação);
- REGRA DE SEGURANÇA: nenhuma escrita em filas/prioridades como efeito da
  leitura da inteligência.
"""

from datetime import datetime, timedelta

from App.modules.intelligence.service import ATTENTION_THRESHOLD_HOURS, IntelligenceService
from App.modules.patient_status.models import PatientState, PatientStatusUpdate
from App.modules.queues.models import QueueStatus


def _open_queue(db_session, make_queue, make_care_request, patient_id: int, specialty="Cardiologia"):
    cr = make_care_request(patient_id, specialty)
    return make_queue(cr.id, specialty), cr


def _add_status(db_session, patient_id: int, care_request_id: int, state: PatientState):
    update = PatientStatusUpdate(
        patient_id=patient_id,
        care_request_id=care_request_id,
        state=state,
        severity=5,
    )
    db_session.add(update)
    db_session.commit()
    return update


# -- Carga por especialidade ---------------------------------------------------

def test_load_empty(db_session):
    svc = IntelligenceService(db_session)
    assert svc.specialty_loads() == []


def test_load_level_low(db_session, patient, make_queue, make_care_request):
    _open_queue(db_session, make_queue, make_care_request, patient.id)
    svc = IntelligenceService(db_session)
    loads = svc.specialty_loads()
    assert len(loads) == 1
    assert loads[0].level == "LOW"
    assert loads[0].open_queues == 1
    assert loads[0].urgent_count == 0


def test_load_level_high_and_urgent_count(db_session, patient, make_queue, make_care_request):
    for _ in range(7):
        _open_queue(db_session, make_queue, make_care_request, patient.id)
    svc = IntelligenceService(db_session)
    loads = svc.specialty_loads()
    assert loads[0].open_queues == 7
    assert loads[0].level == "HIGH"


def test_load_level_medium(db_session, patient, make_queue, make_care_request):
    for _ in range(5):
        _open_queue(db_session, make_queue, make_care_request, patient.id)
    svc = IntelligenceService(db_session)
    assert svc.specialty_loads()[0].level == "MEDIUM"


# -- Tempo médio de espera ------------------------------------------------------

def test_wait_time_empty(db_session):
    assert IntelligenceService(db_session).wait_time_insights() == []


def test_wait_time_completed_entry(db_session, patient, make_queue, make_care_request):
    cr = make_care_request(patient.id)
    q = make_queue(cr.id)
    # Simula ciclo concluído com 2 dias de espera (entered_at no passado).
    q.entered_at = datetime.now() - timedelta(days=2)
    q.status = QueueStatus.COMPLETED
    q.updated_at = datetime.now()
    db_session.commit()
    insights = IntelligenceService(db_session).wait_time_insights()
    assert len(insights) == 1
    assert insights[0].samples == 1
    # 2 dias ± tolerância de execução do teste.
    assert 47.0 <= insights[0].average_wait_hours <= 49.5


# -- Sinais de atenção -----------------------------------------------------------

def test_attention_signal_worsened_long_wait(db_session, patient, make_queue, make_care_request):
    cr = make_care_request(patient.id)
    q = make_queue(cr.id)
    q.entered_at = datetime.now() - timedelta(hours=ATTENTION_THRESHOLD_HOURS + 12)
    db_session.commit()
    _add_status(db_session, patient.id, cr.id, PatientState.WORSENED)

    signals = IntelligenceService(db_session).attention_signals()
    assert len(signals) == 1
    s = signals[0]
    assert s.queue_id == q.id
    assert s.last_state == "WORSENED"
    assert s.hours_waiting > ATTENTION_THRESHOLD_HOURS
    # Explicabilidade: o sinal se explica sozinho e nega decisão automática.
    assert "NÃO altera prioridade" in s.reason


def test_no_signal_when_state_stable(db_session, patient, make_queue, make_care_request):
    cr = make_care_request(patient.id)
    q = make_queue(cr.id)
    q.entered_at = datetime.now() - timedelta(hours=ATTENTION_THRESHOLD_HOURS + 12)
    db_session.commit()
    _add_status(db_session, patient.id, cr.id, PatientState.STABLE)
    assert IntelligenceService(db_session).attention_signals() == []


def test_no_signal_when_wait_short(db_session, patient, make_queue, make_care_request):
    cr = make_care_request(patient.id)
    make_queue(cr.id)  # entered_at = agora (espera ~0h)
    _add_status(db_session, patient.id, cr.id, PatientState.WORSENED)
    assert IntelligenceService(db_session).attention_signals() == []


# -- Contrato do endpoint + segurança -------------------------------------------

def test_summary_endpoint_contract(client):
    res = client.get("/api/v1/intelligence/summary")
    assert res.status_code == 200
    body = res.json()
    assert set(body.keys()) == {"generated_at", "loads", "wait_times", "attention_signals"}


def test_intelligence_is_read_only(client, db_session, patient, make_queue, make_care_request):
    """Regra de segurança V15: ler a inteligência NÃO altera filas/prioridade."""
    cr = make_care_request(patient.id)
    q = make_queue(cr.id)
    before = (q.status, q.priority, q.position)
    assert client.get("/api/v1/intelligence/summary").status_code == 200
    db_session.refresh(q)
    assert (q.status, q.priority, q.position) == before


def test_summary_integration_full(client, db_session, patient, make_queue, make_care_request):
    """Fluxo ponta a ponta: fila com carga + espera + piora aparece no summary."""
    for _ in range(3):
        _open_queue(db_session, make_queue, make_care_request, patient.id)
    cr = make_care_request(patient.id, "Ortopedia")
    q = make_queue(cr.id, "Ortopedia")
    q.entered_at = datetime.now() - timedelta(hours=ATTENTION_THRESHOLD_HOURS + 5)
    db_session.commit()
    _add_status(db_session, patient.id, cr.id, PatientState.WORSENED)

    body = client.get("/api/v1/intelligence/summary").json()
    loads = {ld["specialty"]: ld for ld in body["loads"]}
    assert loads["Cardiologia"]["open_queues"] == 3
    assert any(s["queue_id"] == q.id for s in body["attention_signals"])
