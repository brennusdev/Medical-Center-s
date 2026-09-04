"""MED V3 — Care requests router. Kept thin: HTTP only, logic lives in service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.care_requests.schemas import CareRequestCreate, CareRequestRead
from App.modules.care_requests.service import CareRequestService, NotFoundError, ValidationError

router = APIRouter(prefix="/care-requests", tags=["care-requests"])


def get_service(db: Session = Depends(get_db)) -> CareRequestService:
    return CareRequestService(db)


@router.post(
    "",
    response_model=CareRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar solicitação de atendimento ('Preciso de atendimento')",
)
def create_care_request(payload: CareRequestCreate, service: CareRequestService = Depends(get_service)):
    """Cria a solicitação registrando apenas o RELATO do paciente.
    O sistema não diagnostica nem define prioridade clínica."""
    try:
        return service.create(payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/patient/{patient_id}",
    response_model=list[CareRequestRead],
    summary="Listar solicitações de atendimento de um paciente",
)
def list_care_requests(patient_id: int, service: CareRequestService = Depends(get_service)):
    try:
        return service.list_by_patient(patient_id)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/{request_id}",
    response_model=CareRequestRead,
    summary="Detalhar uma solicitação de atendimento",
)
def get_care_request(request_id: int, service: CareRequestService = Depends(get_service)):
    try:
        return service.get(request_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
