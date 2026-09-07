"""MED V6 — Medical evaluations router. Thin: HTTP only, logic lives in service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.auth.dependencies import get_current_user
from App.modules.medical_evaluations.schemas import (
    MedicalEvaluationCreate,
    MedicalEvaluationRead,
)
from App.modules.medical_evaluations.service import (
    AuthorizationError,
    MedicalEvaluationService,
    NotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/medical-evaluations", tags=["medical-evaluations"])


def get_service(db: Session = Depends(get_db)) -> MedicalEvaluationService:
    return MedicalEvaluationService(db)


@router.post(
    "",
    response_model=MedicalEvaluationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar avaliação profissional (texto literal do profissional)",
)
def create_evaluation(
    payload: MedicalEvaluationCreate,
    current=Depends(get_current_user),
    service: MedicalEvaluationService = Depends(get_service),
):
    """Cria uma AVALIAÇÃO PROFISSIONAL referenciando o relato original, que
    permanece intacto. O sistema não interpreta nem diagnostica automaticamente.

    V9: com token, o professional_id é derivado do usuário autenticado —
    um profissional não pode registrar avaliação em nome de outro.
    """
    if current is not None:
        payload.professional_id = current.id
    try:
        return service.create(payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/request/{care_request_id}",
    response_model=list[MedicalEvaluationRead],
    summary="Histórico de avaliações de um atendimento",
)
def list_request_evaluations(care_request_id: int, service: MedicalEvaluationService = Depends(get_service)):
    try:
        return service.list_by_care_request(care_request_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/{evaluation_id}",
    response_model=MedicalEvaluationRead,
    summary="Detalhar uma avaliação",
)
def get_evaluation(evaluation_id: int, service: MedicalEvaluationService = Depends(get_service)):
    try:
        return service.get(evaluation_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
