"""MED V8 — Router de Analytics.

Router fino: só HTTP (validação de params, status codes, delegação).
As regras (janela válida, normalização) estão no service; o SQL está no
repository. Em V9 estes endpoints passam a exigir autenticação (ADMIN/HOSPITAL)
via dependencies — a assinatura é mantida estável para o frontend.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.analytics.schemas import (
    AnalyticsFilters,
    AppointmentPeriodMetric,
    GroupCount,
    OverviewMetrics,
    PriorityDistribution,
    WaitTimeMetric,
)
from App.modules.analytics.service import AnalyticsService, ValidationError

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


def _filters(
    start_date: date | None = Query(None, description="Início da janela (inclusivo)"),
    end_date: date | None = Query(None, description="Fim da janela (inclusivo)"),
    specialty: str | None = Query(None, max_length=100),
    hospital_id: int | None = Query(None, gt=0),
) -> AnalyticsFilters:
    """Monta os filtros comuns; erros de janela viram 422 no service."""
    return AnalyticsFilters(
        start_date=start_date, end_date=end_date, specialty=specialty, hospital_id=hospital_id
    )


@router.get("/overview", response_model=OverviewMetrics, summary="Volumes gerais do sistema")
def overview(filters: AnalyticsFilters = Depends(_filters), service: AnalyticsService = Depends(get_service)):
    try:
        return service.overview(filters)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/specialties", response_model=list[GroupCount], summary="Solicitações por especialidade")
def specialties(filters: AnalyticsFilters = Depends(_filters), service: AnalyticsService = Depends(get_service)):
    try:
        return service.specialties(filters)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/hospitals", response_model=list[GroupCount], summary="Filas por hospital")
def hospitals(filters: AnalyticsFilters = Depends(_filters), service: AnalyticsService = Depends(get_service)):
    try:
        return service.hospitals(filters)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/wait-times", response_model=WaitTimeMetric, summary="Tempo médio de espera (horas)")
def wait_times(filters: AnalyticsFilters = Depends(_filters), service: AnalyticsService = Depends(get_service)):
    try:
        return service.wait_times(filters)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/priorities", response_model=list[PriorityDistribution], summary="Distribuição de prioridades ativas")
def priorities(filters: AnalyticsFilters = Depends(_filters), service: AnalyticsService = Depends(get_service)):
    try:
        return service.priorities(filters)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/appointments", response_model=list[AppointmentPeriodMetric], summary="Consultas por período (dia)")
def appointments_by_period(
    filters: AnalyticsFilters = Depends(_filters), service: AnalyticsService = Depends(get_service)
):
    try:
        return service.appointments_by_period(filters)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
