"""MED V4 — Business rules for queues and prioritization.

REGRAS DE SEGURANÇA (obrigatórias):
- A prioridade operacional NÃO representa diagnóstico médico.
- O sistema NÃO diagnostica o paciente e NÃO decide sozinho uma prioridade
  clínica definitiva. Toda prioridade é atribuída explicitamente por um
  usuário autorizado do domínio (não-PATIENT) e registrada com actor_id.
- O paciente NÃO pode alterar a própria prioridade.
- O histórico (QueueEvent) é append-only: nunca é apagado pela aplicação.

Regras de negócio aplicadas:
1. Uma CareRequest não pode possuir mais de uma entrada ATIVA na mesma fila.
2. Toda entrada nova recebe posição (fim da fila ativa da especialidade).
3. Toda alteração relevante cria QueueEvent (append-only).
4. Alteração de posição registra posição anterior e nova.
5. Alteração de prioridade registra prioridade anterior e nova.
6. Alteração de status registra evento.
7. Saída da fila (REMOVED/COMPLETED) registra evento.
8. Histórico nunca é apagado pela lógica normal da aplicação.

Ordenação determinística (após mudança de prioridade):
- URGENT > HIGH > MEDIUM > NORMAL (peso 4/3/2/1);
- dentro da mesma prioridade: menor entered_at primeiro;
- posições renumeradas 1..N nas entradas ativas, gerando POSITION_CHANGED
  para cada item cuja posição mudou.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from App.modules.queues.models import Queue, QueueEvent, QueueEventType, QueuePriority, QueueStatus
from App.modules.queues.repository import QueueRepository
from App.modules.queues.schemas import QueueCreate

# Pesos da prioridade operacional (maior = mais prioritário)
PRIORITY_WEIGHT: dict[QueuePriority, int] = {
    QueuePriority.NORMAL: 1,
    QueuePriority.MEDIUM: 2,
    QueuePriority.HIGH: 3,
    QueuePriority.URGENT: 4,
}

# Status que indicam que a entrada deixou de estar "ativa" na fila
INACTIVE_STATUSES = (QueueStatus.REMOVED, QueueStatus.COMPLETED)


class NotFoundError(Exception):
    """Requested entity does not exist."""


class ValidationError(Exception):
    """Business rule violation."""


class AuthorizationError(Exception):
    """Actor not allowed to perform the operation."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class QueueService:
    def __init__(self, db: Session) -> None:
        self.repo = QueueRepository(db)
        self.db = db

    # -- Helpers -------------------------------------------------------------
    def _event(
        self,
        queue_id: int,
        event_type: QueueEventType,
        *,
        previous_position: int | None = None,
        new_position: int | None = None,
        previous_priority: QueuePriority | None = None,
        new_priority: QueuePriority | None = None,
        description: str = "",
        actor_id: int | None = None,
    ) -> QueueEvent:
        return self.repo.add_event(
            QueueEvent(
                queue_id=queue_id,
                event_type=event_type,
                previous_position=previous_position,
                new_position=new_position,
                previous_priority=previous_priority,
                new_priority=new_priority,
                description=description,
                actor_id=actor_id,
            )
        )

    # -- Criação --------------------------------------------------------------
    def create(self, data: QueueCreate) -> Queue:
        care_request = self.repo.get_care_request(data.care_request_id)
        if care_request is None:
            raise NotFoundError(f"Solicitação de atendimento {data.care_request_id} não encontrada")

        if data.actor_id is not None and self.repo.get_user(data.actor_id) is None:
            raise NotFoundError(f"Usuário {data.actor_id} não encontrado")

        specialty = data.specialty.strip()
        duplicate = self.repo.find_active_by_care_request(data.care_request_id, specialty)
        if duplicate is not None:
            raise ValidationError(
                f"A solicitação {data.care_request_id} já possui uma entrada ativa na fila de {specialty}"
            )

        # Posição inicial: fim da fila ativa da especialidade (determinística).
        active = self.repo.list_active_by_specialty(specialty)
        position = (max(q.position for q in active) + 1) if active else 1

        queue = Queue(
            care_request_id=data.care_request_id,
            specialty=specialty,
            hospital_id=data.hospital_id,
            status=QueueStatus.WAITING,
            priority=QueuePriority.NORMAL,  # nunca automática; prioridade clínica não cabe ao sistema
            position=position,
        )
        created = self.repo.create(queue)
        self._event(
            created.id,
            QueueEventType.CREATED,
            new_position=created.position,
            new_priority=created.priority,
            description=f"Entrada criada na fila de {specialty} (posição {created.position})",
            actor_id=data.actor_id,
        )
        return created

    # -- Consultas -------------------------------------------------------------
    def get(self, queue_id: int) -> Queue:
        queue = self.repo.get(queue_id)
        if queue is None:
            raise NotFoundError(f"Entrada de fila {queue_id} não encontrada")
        return queue

    def list_by_patient(self, patient_id: int) -> list[Queue]:
        if patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")
        return self.repo.list_by_patient(patient_id)

    def list_events(self, queue_id: int) -> list[QueueEvent]:
        self.get(queue_id)  # 404 se a fila não existir
        return self.repo.list_events(queue_id)

    # -- Reorganização determinística -----------------------------------------
    def _reorganize(self, specialty: str, actor_id: int | None) -> list[int]:
        """Renumera posições das entradas ativas da especialidade.

        Ordenação: peso da prioridade (desc), depois entered_at (asc) e id (asc)
        como desempate determinístico. Gera POSITION_CHANGED para cada item
        cujo (id, nova posição) difere do anterior. Retorna os ids afetados.
        """
        affected: list[int] = []
        active = self.repo.list_active_by_specialty(specialty)
        ordered = sorted(
            active,
            key=lambda q: (-PRIORITY_WEIGHT[q.priority], q.entered_at or _utcnow(), q.id),
        )
        for index, queue in enumerate(ordered, start=1):
            if queue.position != index:
                previous = queue.position
                queue.position = index
                queue.updated_at = _utcnow()
                self._event(
                    queue.id,
                    QueueEventType.POSITION_CHANGED,
                    previous_position=previous,
                    new_position=index,
                    description=f"Reorganização da fila de {specialty}: {previous} -> {index}",
                    actor_id=actor_id,
                )
                affected.append(queue.id)
        if affected:
            self.db.commit()
        return affected

    # -- Alteração de prioridade ------------------------------------------------
    def update_priority(self, queue_id: int, new_priority: QueuePriority, actor_id: int) -> Queue:
        queue = self.get(queue_id)

        user = self.repo.get_user(actor_id)
        if user is None:
            raise NotFoundError(f"Usuário {actor_id} não encontrado")
        if user.role == "PATIENT":
            # Regra 13: o paciente não pode alterar sua própria prioridade.
            # Nesta versão (sem JWT), autorização = papel do ator informado.
            raise AuthorizationError("Pacientes não podem alterar prioridades")
        if getattr(user, "role", "") not in ("RECEPTIONIST", "NURSE", "DOCTOR", "ADMIN"):
            raise AuthorizationError(f"Papel {user.role} não está autorizado a alterar prioridade")

        if queue.priority == new_priority:
            return queue  # nada muda: sem evento, sem reorganização

        previous_priority = queue.priority
        queue.priority = new_priority
        queue.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(queue)

        self._event(
            queue.id,
            QueueEventType.PRIORITY_CHANGED,
            previous_priority=previous_priority,
            new_priority=new_priority,
            description=f"Prioridade alterada de {previous_priority.value} para {new_priority.value}",
            actor_id=actor_id,
        )
        self._reorganize(queue.specialty, actor_id)
        self.db.refresh(queue)
        return queue
