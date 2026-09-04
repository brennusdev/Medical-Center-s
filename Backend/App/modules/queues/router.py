"""MED V4 — Queues router. Kept thin: HTTP only, logic lives in service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.queues.schemas import (
    QueueCreate,
    QueueEventRead,
    QueuePriorityUpdate,
    QueueRead,
)
from App.modules.queues.service import (
    AuthorizationError,
    NotFoundError,
    QueueService,
    ValidationError,
)

router = APIRouter(prefix="/queues", tags=["queues"])


def get_service(db: Session = Depends(get_db)) -> QueueService:
    return QueueService(db)


@router.post(
    "",
    response_model=QueueRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar entrada na fila (status WAITING, prioridade NORMAL)",
)
def create_queue(payload: QueueCreate, service: QueueService = Depends(get_service)):
    """Cria a entrada na fila com posição calculada. O sistema NÃO atribui
    prioridade clínica automática: prioridade inicial é sempre NORMAL."""
    try:
        return service.create(payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/patient/{patient_id}",
    response_model=list[QueueRead],
    summary="Listar entradas de fila de um paciente (todas as especialidades)",
)
def list_patient_queues(patient_id: int, service: QueueService = Depends(get_service)):
    try:
        return service.list_by_patient(patient_id)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/{queue_id}",
    response_model=QueueRead,
    summary="Detalhar uma entrada na fila",
)
def get_queue(queue_id: int, service: QueueService = Depends(get_service)):
    try:
        return service.get(queue_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/{queue_id}/events",
    response_model=list[QueueEventRead],
    summary="Histórico (timeline) imutável da entrada na fila",
)
def get_queue_events(queue_id: int, service: QueueService = Depends(get_service)):
    try:
        return service.list_events(queue_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch(
    "/{queue_id}/priority",
    response_model=QueueRead,
    summary="Alterar prioridade (somente usuários autorizados; paciente não pode)",
)
def update_queue_priority(
    queue_id: int, payload: QueuePriorityUpdate, service: QueueService = Depends(get_service)
):
    """Altera a prioridade operacional (não clínica) e reorganiza a fila
    de forma determinística, registrando eventos com o ator responsável."""
    try:
        return service.update_priority(queue_id, payload.priority, payload.actor_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
