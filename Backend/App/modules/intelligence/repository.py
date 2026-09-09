"""MED V15 — Repository do módulo intelligence.

Somente leitura (SELECT/agregação). Nenhuma escrita: inteligência operacional
é read-only sobre o estado transacional — se um dia precisar derivar algo,
será materializado em tabela própria, nunca mutando filas/consultas.
"""

from datetime import datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from App.modules.appointments.models import Appointment
from App.modules.care_requests.models import CareRequest
from App.modules.patient_status.models import PatientState, PatientStatusUpdate
from App.modules.queues.models import Queue, QueuePriority, QueueStatus


class IntelligenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def open_queues_by_specialty(self) -> list[tuple[str, int, int]]:
        """(specialty, abertas, urgentes) — agregação no banco, sem N+1."""
        stmt = (
            select(
                Queue.specialty,
                func.count(),
                func.sum(case((Queue.priority == QueuePriority.URGENT, 1), else_=0)),
            )
            .where(Queue.status.in_([QueueStatus.WAITING, QueueStatus.IN_REVIEW]))
            .group_by(Queue.specialty)
        )
        return [(r[0], int(r[1]), int(r[2] or 0)) for r in self.db.execute(stmt).all()]

    def completed_wait_by_specialty(self) -> list[tuple[str, float, int]]:
        """Espera média (h) de entradas concluídas, por especialidade.

        Usa entered_at → updated_at das concluídas: aproximação operacional
        honesta e barata (a V8 já valida que updated_at acompanha o ciclo).
        """
        stmt = (
            select(
                Queue.specialty,
                func.avg(
                    func.julianday(Queue.updated_at) - func.julianday(Queue.entered_at)
                ),
                func.count(),
            )
            .where(Queue.status == QueueStatus.COMPLETED)
            .group_by(Queue.specialty)
        )
        rows = self.db.execute(stmt).all()
        # SQLite retorna dias (julianday); convertemos para horas (×24).
        return [(r[0], round(float(r[1]) * 24.0, 2), int(r[2])) for r in rows if r[1] is not None]

    def long_waiting_with_worsening(self, min_hours: float) -> list[Queue]:
        """Filas ativas com espera > min_hours e último relato do paciente = WORSENED.

        Subquery: última atualização de estado por care_request (max id —
        append-only, logo o maior id é o mais recente).
        """
        cutoff = datetime.now() - timedelta(hours=min_hours)
        latest = (
            select(
                PatientStatusUpdate.care_request_id,
                func.max(PatientStatusUpdate.id).label("last_id"),
            )
            .group_by(PatientStatusUpdate.care_request_id)
            .subquery()
        )
        stmt = (
            select(Queue)
            .join(PatientStatusUpdate, PatientStatusUpdate.care_request_id == Queue.care_request_id)
            .join(latest, latest.c.last_id == PatientStatusUpdate.id)
            .where(
                Queue.status.in_([QueueStatus.WAITING, QueueStatus.IN_REVIEW]),
                Queue.entered_at < cutoff,
                PatientStatusUpdate.state == PatientState.WORSENED,
            )
            .order_by(Queue.entered_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def hours_waiting(self, queue: Queue) -> float:
        delta = datetime.now() - queue.entered_at
        return round(max(delta.total_seconds(), 0) / 3600.0, 2)

    def last_state_for(self, care_request_id: int) -> str:
        row = (
            self.db.execute(
                select(PatientStatusUpdate.state)
                .where(PatientStatusUpdate.care_request_id == care_request_id)
                .order_by(PatientStatusUpdate.id.desc())
                .limit(1)
            )
            .scalar_one_or_none()
        )
        return row.value if row is not None else ""

    def patient_of(self, care_request_id: int) -> int:
        return (
            self.db.execute(
                select(CareRequest.patient_id).where(CareRequest.id == care_request_id)
            ).scalar_one_or_none()
            or 0
        )

    def appointments_count(self) -> int:
        return int(self.db.execute(select(func.count()).select_from(Appointment)).scalar() or 0)

    def care_requests_count(self) -> int:
        return int(self.db.execute(select(func.count()).select_from(CareRequest)).scalar() or 0)
