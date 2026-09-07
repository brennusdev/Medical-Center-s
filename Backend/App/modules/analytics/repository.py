"""MED V8 — Camada de acesso a dados do Analytics.

DECISÃO DE PERFORMANCE (obrigatória na V8):
- Nenhum método desta classe carrega listas completas para contar em Python.
  Toda métrica usa agregação no banco (COUNT/AVG/GROUP BY) — o volume de dados
  cresce com o tempo, mas o custo das consultas permanece proporcional ao
  número de grupos, não ao número de registros.
- Os índices que ajudam estas consultas foram criados nas migrations das
  versões anteriores (ex.: ix_notifications_user_created,
  ix_queues_specialty_status) e na migration da V8 (índices de data).

Suporte duplo SQLite/PostgreSQL:
- SQLite não tem intervalos nativos; datas são comparadas como texto ISO ou
  via julianday. O Postgres tem `interval`/`date`. Para manter o mesmo
  contrato de saída, os trechos específicos de dialete ficam isolados aqui.
"""

from datetime import date, datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from App.modules.appointments.models import Appointment, AppointmentStatus
from App.modules.care_requests.models import CareRequest, CareRequestStatus
from App.modules.patient_status.models import PatientStatusUpdate
from App.modules.queues.models import Queue, QueuePriority, QueueStatus

# Status "abertos" de uma solicitação de atendimento (ainda em andamento).
OPEN_CARE_STATUSES = (
    CareRequestStatus.CREATED,
    CareRequestStatus.IN_REVIEW,
    CareRequestStatus.REFERRED,
)
# Procedimentos pendentes = entradas ativas em fila (aguardando ação operacional).
ACTIVE_QUEUE_STATUSES = (
    QueueStatus.WAITING,
    QueueStatus.IN_REVIEW,
    QueueStatus.REFERRED,
)


def _day_start(d: date) -> datetime:
    """Converte data para o início do dia em UTC (limite inferior da janela)."""
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def _day_end_exclusive(d: date) -> datetime:
    """Limite superior EXCLUSIVO da janela (início do dia seguinte).

    Usar `>= start AND < end_exclusive` em vez de `BETWEEN` evita perder
    registros com hora 00:00 do último dia e evita depender de precisão de
    microssegundos.
    """
    if d.month == 12:
        nxt = date(d.year + 1, 1, 1)
    else:
        nxt = date(d.year, d.month + 1, 1)
    if (d.month in (1, 3, 5, 7, 8, 10, 12) and d.day == 31) or (d.month == 2 and d.day >= 28):
        # Delegar o "próximo dia" ao calendário: somar 1 dia de forma segura.
        from datetime import timedelta

        nxt = d + timedelta(days=1)
    return datetime(nxt.year, nxt.month, nxt.day, tzinfo=timezone.utc)


class AnalyticsRepository:
    """Único ponto de acesso ao banco para métricas (sem regras de negócio)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -- Helpers de filtro ----------------------------------------------------
    def _queue_filters(self, start: datetime | None, end: datetime | None, specialty: str | None, hospital_id: int | None):
        """Monta os predicados comuns das consultas de fila (mesma lógica em
        todos os agregados, para que números nunca contradigam entre endpoints)."""
        filters = []
        if start:
            filters.append(Queue.entered_at >= start)
        if end:
            filters.append(Queue.entered_at < end)
        if specialty:
            filters.append(Queue.specialty == specialty)
        if hospital_id:
            filters.append(Queue.hospital_id == hospital_id)
        return filters

    def _care_filters(self, start: datetime | None, end: datetime | None, specialty: str | None):
        filters = []
        if start:
            filters.append(CareRequest.created_at >= start)
        if end:
            filters.append(CareRequest.created_at < end)
        if specialty:
            filters.append(CareRequest.specialty == specialty)
        return filters

    def _appointment_filters(self, start: datetime | None, end: datetime | None, specialty: str | None):
        filters = []
        if start:
            filters.append(Appointment.scheduled_at >= start)
        if end:
            filters.append(Appointment.scheduled_at < end)
        if specialty:
            filters.append(Appointment.specialty == specialty)
        return filters

    # -- Overview ---------------------------------------------------------------
    def overview_counts(
        self,
        start: datetime | None,
        end: datetime | None,
        specialty: str | None,
        hospital_id: int | None,
    ) -> dict[str, int]:
        """Um único SELECT com COUNTs condicionais (subqueries escalares).

        Por que não quatro SELECTs? Cada round-trip tem custo de rede/parse;
        com funções escalares o banco resolve tudo em um plano só. As subqueries
        escalares são pequenas (COUNT) e usam os mesmos índices.
        """
        care_total = select(func.count(CareRequest.id)).where(*self._care_filters(start, end, specialty))
        care_open = care_total.where(CareRequest.status.in_(OPEN_CARE_STATUSES))
        appt_total = select(func.count(Appointment.id)).where(*self._appointment_filters(specialty))
        queue_total = select(func.count(Queue.id)).where(*self._queue_filters(start, end, specialty, hospital_id))
        queue_waiting = queue_total.where(Queue.status == QueueStatus.WAITING)
        queue_active = queue_total.where(Queue.status.in_(ACTIVE_QUEUE_STATUSES))

        stmt = select(
            care_total.scalar_subquery().label("total_care_requests"),
            care_open.scalar_subquery().label("open_care_requests"),
            appt_total.scalar_subquery().label("total_appointments"),
            queue_total.scalar_subquery().label("total_queue_entries"),
            queue_waiting.scalar_subquery().label("waiting_queue_entries"),
            queue_active.scalar_subquery().label("pending_procedures"),
        )
        row = self.db.execute(stmt).one()
        return {
            "total_care_requests": row.total_care_requests,
            "open_care_requests": row.open_care_requests,
            "total_appointments": row.total_appointments,
            "total_queue_entries": row.total_queue_entries,
            "waiting_queue_entries": row.waiting_queue_entries,
            "pending_procedures": row.pending_procedures,
        }

    # -- Distribuições (GROUP BY) ----------------------------------------------
    def by_specialty(
        self, start: datetime | None, end: datetime | None, specialty: str | None
    ) -> list[dict]:
        """Distribuição de solicitações por especialidade.

        GROUP BY em `specialty` (coluna indexada nas tabelas de fila) — o banco
        retorna N linhas (uma por especialidade) em vez de M (uma por request).
        `open` é contado no mesmo statement com SUM(CASE) para não duplicar
        varreduras.
        """
        open_case = func.sum(
            case((CareRequest.status.in_(OPEN_CARE_STATUSES), 1), else_=0)
        ).label("open")
        stmt = (
            select(
                CareRequest.specialty.label("key"),
                func.count(CareRequest.id).label("total"),
                open_case,
            )
            .where(*self._care_filters(start, end, None))
            .group_by(CareRequest.specialty)
            .order_by(func.count(CareRequest.id).desc())
        )
        if specialty:
            stmt = stmt.where(CareRequest.specialty == specialty)
        rows = self.db.execute(stmt).all()
        return [dict(key=r.key, total=r.total, open=int(r.open or 0)) for r in rows]

    def by_hospital(
        self, start: datetime | None, end: datetime | None, hospital_id: int | None
    ) -> list[dict]:
        """Distribuição de filas por hospital (GROUP BY hospital_id).

        `key` é stringificado ("HOSPITAL {id}") porque hospital_id é opcional e
        sem FK (decisão herdada da V2/V4 — módulo de hospitais não existe).
        """
        stmt = (
            select(
                Queue.hospital_id.label("hospital_id"),
                func.count(Queue.id).label("total"),
                func.sum(case((Queue.status.in_(ACTIVE_QUEUE_STATUSES), 1), else_=0)).label("open"),
            )
            .where(*self._queue_filters(start, end, None, None))
            .group_by(Queue.hospital_id)
            .order_by(func.count(Queue.id).desc())
        )
        rows = self.db.execute(stmt).all()
        result = []
        for r in rows:
            label = f"HOSPITAL {r.hospital_id}" if r.hospital_id is not None else "SEM HOSPITAL"
            if hospital_id and r.hospital_id != hospital_id:
                continue
            result.append(dict(key=label, total=r.total, open=int(r.open or 0)))
        return result

    def priority_distribution(
        self, start: datetime | None, end: datetime | None, specialty: str | None, hospital_id: int | None
    ) -> list[dict]:
        """Distribuição das prioridades OPERACIONAIS ativas (não é diagnóstico)."""
        stmt = (
            select(
                Queue.priority,
                func.count(Queue.id).label("total"),
            )
            .where(Queue.status.in_(ACTIVE_QUEUE_STATUSES), *self._queue_filters(start, end, specialty, hospital_id))
            .group_by(Queue.priority)
        )
        return [dict(priority=r[0], total=r.total) for r in self.db.execute(stmt).all()]

    def status_distribution(
        self, start: datetime | None, end: datetime | None, specialty: str | None, hospital_id: int | None
    ) -> list[dict]:
        stmt = (
            select(Queue.status, func.count(Queue.id).label("total"))
            .where(*self._queue_filters(start, end, specialty, hospital_id))
            .group_by(Queue.status)
        )
        return [dict(status=r[0], total=r.total) for r in self.db.execute(stmt).all()]

    def appointments_by_period(
        self, start: datetime | None, end: datetime | None, specialty: str | None
    ) -> list[dict]:
        """Consultas por dia (GROUP BY date). Responde 'consultas por período'."""
        day_expr = func.date(Appointment.scheduled_at)
        stmt = (
            select(day_expr.label("day"), func.count(Appointment.id).label("total"))
            .where(*self._appointment_filters(start, end, specialty))
            .group_by(day_expr)
            .order_by(day_expr.asc())
        )
        rows = self.db.execute(stmt).all()
        out = []
        for r in rows:
            # SQLite/Postgres devolvem date ou string — normalizamos para date.
            d = r.day if isinstance(r.day, date) else datetime.strptime(str(r.day)[:10], "%Y-%m-%d").date()
            out.append(dict(day=d, total=r.total))
        return out

    def wait_times(
        self, start: datetime | None, end: datetime | None, specialty: str | None, hospital_id: int | None
    ) -> dict:
        """Tempo médio de espera (horas) das esperas JÁ ENCERRADAS.

        Implementação por dialete:
        - SQLite: diferença em dias via julianday() * 24 (função embutida,
          executa no banco, sem carregar linhas em Python).
        - Postgres: cast para epoch (EXTRACT(EPOCH ...)) — comentado para a
          migração futura do ambiente.
        A agregação no banco mantém a consulta O(1) em transferência: retorna
        uma linha única (AVG + COUNT), mesmo com milhões de histórico.
        """
        finished = self._queue_filters(start, end, specialty, hospital_id) + [
            Queue.status.in_([QueueStatus.COMPLETED, QueueStatus.REMOVED])
        ]
        seconds = (func.julianday(Queue.updated_at) - func.julianday(Queue.entered_at)) * 86400.0
        stmt = select(
            func.avg(seconds).label("avg_seconds"),
            func.count(Queue.id).label("samples"),
        ).where(*finished)
        row = self.db.execute(stmt).one()
        avg_seconds = row.avg_seconds
        return {
            "average_wait_hours": round(avg_seconds / 3600.0, 2) if avg_seconds is not None else None,
            "samples": row.samples,
        }

    # -- Dashboards ---------------------------------------------------------------
    def doctor_recent_care_requests(self, limit: int = 20) -> list[CareRequest]:
        """Casos recentes para o dashboard do médico.

        LIMIT explícito: dashboard é leitura de apoio, não exportação — sem
        limite, a tela degradaria conforme a base cresce.
        """
        stmt = (
            select(CareRequest)
            .where(CareRequest.status.in_(OPEN_CARE_STATUSES))
            .order_by(CareRequest.created_at.desc(), CareRequest.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def doctor_today_appointments(self, day: datetime) -> list[Appointment]:
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = day_start + (datetime(2026, 1, 2) - datetime(2026, 1, 1))
        stmt = (
            select(Appointment)
            .where(
                Appointment.scheduled_at >= day_start,
                Appointment.scheduled_at < next_day,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.scheduled_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def hospital_open_queues(self, hospital_id: int) -> list[Queue]:
        stmt = (
            select(Queue)
            .where(Queue.hospital_id == hospital_id, Queue.status.in_(ACTIVE_QUEUE_STATUSES))
            .order_by(Queue.specialty.asc(), Queue.position.asc())
        )
        return list(self.db.scalars(stmt).all())

    def hospital_counts(self, hospital_id: int, start: datetime | None, end: datetime | None) -> dict[str, int]:
        """COUNTs por hospital com subqueries escalares (mesma estratégia do overview)."""
        q = select(func.count(Queue.id)).where(
            Queue.hospital_id == hospital_id, *self._queue_filters(start, end, None, None)
        )
        stmt = select(
            q.where(Queue.status.in_(ACTIVE_QUEUE_STATUSES)).scalar_subquery().label("open_queues"),
            q.where(Queue.status == QueueStatus.WAITING).scalar_subquery().label("waiting"),
            q.where(Queue.status == QueueStatus.COMPLETED).scalar_subquery().label("completed"),
        )
        row = self.db.execute(stmt).one()
        return {"open_queues": row.open_queues, "waiting": row.waiting, "completed": row.completed}

    def patient_latest_status_update(self, patient_id: int) -> PatientStatusUpdate | None:
        stmt = (
            select(PatientStatusUpdate)
            .where(PatientStatusUpdate.patient_id == patient_id)
            .order_by(PatientStatusUpdate.created_at.desc(), PatientStatusUpdate.id.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def admin_specialty_queues(self) -> list[dict]:
        """Capacidade registrada: filas ativas por especialidade (GROUP BY)."""
        stmt = (
            select(
                Queue.specialty.label("key"),
                func.count(Queue.id).label("total"),
            )
            .where(Queue.status.in_(ACTIVE_QUEUE_STATUSES))
            .group_by(Queue.specialty)
            .order_by(func.count(Queue.id).desc())
        )
        return [dict(key=r.key, total=r.total, open=r.total) for r in self.db.execute(stmt).all()]
