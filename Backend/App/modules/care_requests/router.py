"""MED V3 — Care requests router. Kept thin: HTTP only, logic lives in service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.auth.dependencies import check_ownership, get_current_user
from App.modules.care_requests.schemas import CareRequestCreate, CareRequestRead
from App.modules.care_requests.service import CareRequestService, NotFoundError, ValidationError

# MED V9: o router continua fino, mas declara as exigências de segurança.
# O usuário autenticado (token) é resolvido pela dependency; sem token, o
# modo legado preserva o comportamento V1–V8 (ver dependencies.py).

router = APIRouter(prefix="/care-requests", tags=["care-requests"])


def get_service(db: Session = Depends(get_db)) -> CareRequestService:
    return CareRequestService(db)


@router.post(
    "",
    response_model=CareRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar solicitação de atendimento ('Preciso de atendimento')",
)
def create_care_request(
    payload: CareRequestCreate,
    user=Depends(get_current_user),
    service: CareRequestService = Depends(get_service),
):
    """Cria a solicitação registrando apenas o RELATO do paciente.
    O sistema não diagnostica nem define prioridade clínica.

    V9 (ownership): se o chamador veio autenticado via token, um PATIENT só
    pode criar solicitação para SI MESMO (patient_id do payload é ignorado em
    favor do token quando divergente) — o cliente não é fonte de verdade.
    """
    if user is not None and user.role == "PATIENT":
        payload.patient_id = user.id  # derivado do token, não do cliente
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
def list_care_requests(patient_id: int, user=Depends(get_current_user), service: CareRequestService = Depends(get_service)):
    # V9 ownership: paciente autenticado só lista as próprias solicitações.
    check_ownership(user, patient_id)
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
