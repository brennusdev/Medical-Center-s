"""MED V4 — Data access layer for queues (no business rules here)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from App.modules.care_requests.models import CareRequest
from App.modules.queues.models import Queue, QueueEvent, QueueStatus
from App.modules.users.models import User


class QueueRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- Queue --------------------------------------------------------------
    def create(self, queue: Queue) -> Queue:
        self.db.add(queue)
        self.db.commit()
        self.db.refresh(queue)
        return queue

    def get(self, queue_id: int) -> Queue | None:
        return self.db.get(Queue, queue_id)

    def list_by_patient(self, patient_id: int) -> list[Queue]:
        stmt = (
            select(Queue)
            .join(CareRequest, Queue.care_request_id == CareRequest.id)
            .where(CareRequest.patient_id == patient_id)
            .order_by(Queue.position.asc(), Queue.entered_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def find_active_by_care_request(self, care_request_id: int, specialty: str) -> Queue | None:
        """Entrada ativa da mesma CareRequest na mesma especialidade (regra de duplicidade)."""
        stmt = (
            select(Queue)
            .where(
                Queue.care_request_id == care_request_id,
                Queue.specialty == specialty,
                Queue.status.notin_([QueueStatus.REMOVED, QueueStatus.COMPLETED]),
            )
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def list_active_by_specialty(self, specialty: str) -> list[Queue]:
        """Entradas ativas (WAITING/IN_REVIEW/REFERRED/SCHEDULED) de uma especialidade."""
        stmt = (
            select(Queue)
            .where(
                Queue.specialty == specialty,
                Queue.status.notin_([QueueStatus.REMOVED, QueueStatus.COMPLETED]),
            )
            .order_by(Queue.position.asc())
        )
        return list(self.db.scalars(stmt).all())

    # -- QueueEvent (append-only: nunca apagar/atualizar pela aplicação) ----
    def add_event(self, event: QueueEvent) -> QueueEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_events(self, queue_id: int) -> list[QueueEvent]:
        stmt = (
            select(QueueEvent)
            .where(QueueEvent.queue_id == queue_id)
            .order_by(QueueEvent.created_at.asc(), QueueEvent.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    # -- MED V11 — paginação do histórico (append-only cresce sem limite) ------
    def list_events_paged(
        self, queue_id: int, limit: int = 50, offset: int = 0
    ) -> tuple[list[QueueEvent], int]:
        """Histórico paginado com total exato.

        QueueEvent é append-only — em meses de operação uma entrada pode ter
        centenas de eventos; carregar tudo em cada consulta de timeline seria
        desperdício. Page-based mantém o contrato simples e o COUNT usa o
        índice ix_queue_events_created_at.
        """
        stmt = (
            select(QueueEvent)
            .where(QueueEvent.queue_id == queue_id)
            .order_by(QueueEvent.created_at.asc(), QueueEvent.id.asc())
            .limit(limit)
            .offset(offset)
        )
        items = list(self.db.scalars(stmt).all())
        total = self.db.scalar(
            select(func.count()).select_from(QueueEvent).where(QueueEvent.queue_id == queue_id)
        )
        return items, int(total or 0)

    # -- Validação / suporte -------------------------------------------------
    def get_care_request(self, care_request_id: int) -> CareRequest | None:
        return self.db.get(CareRequest, care_request_id)

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)
