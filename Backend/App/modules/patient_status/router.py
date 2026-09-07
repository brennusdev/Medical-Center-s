"""MED V5 — Patient status router. Kept thin: HTTP only, logic lives in service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.auth.dependencies import check_ownership, get_current_user
from App.modules.patient_status.schemas import (
    PatientStatusUpdateCreate,
    PatientStatusUpdateRead,
)
from App.modules.patient_status.service import (
    AuthorizationError,
    NotFoundError,
    PatientStatusService,
    ValidationError,
)

router = APIRouter(prefix="/patient-status", tags=["patient-status"])


def get_service(db: Session = Depends(get_db)) -> PatientStatusService:
    return PatientStatusService(db)


@router.post(
    "",
    response_model=PatientStatusUpdateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar atualização de estado (relato do próprio paciente)",
)
def create_status_update(
    payload: PatientStatusUpdateCreate,
    current=Depends(get_current_user),
    service: PatientStatusService = Depends(get_service),
):
    """Registra o relato do paciente. O sistema não diagnostica, não altera
    prioridade da fila e não altera o status da solicitação.

    V9: paciente autenticado só registra relato para SI mesmo — o
    patient_id do payload é sobrescrito pelo token (cliente não é fonte
    de verdade para identidade).
    """
    if current is not None and current.role == "PATIENT":
        payload.patient_id = current.id
    try:
        return service.create(payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/patient/{patient_id}",
    response_model=list[PatientStatusUpdateRead],
    summary="Histórico de atualizações de estado de um paciente",
)
def list_patient_updates(
    patient_id: int,
    current=Depends(get_current_user),
    service: PatientStatusService = Depends(get_service),
):
    # V9 ownership: histórico de estado é dado sensível do paciente.
    check_ownership(current, patient_id)
    try:
        return service.list_by_patient(patient_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/request/{care_request_id}",
    response_model=list[PatientStatusUpdateRead],
    summary="Atualizações de estado relacionadas a uma solicitação",
)
def list_request_updates(
    care_request_id: int, service: PatientStatusService = Depends(get_service)
):
    try:
        return service.list_by_care_request(care_request_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/{status_id}",
    response_model=PatientStatusUpdateRead,
    summary="Detalhar uma atualização de estado",
)
def get_status_update(status_id: int, service: PatientStatusService = Depends(get_service)):
    try:
        return service.get(status_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
