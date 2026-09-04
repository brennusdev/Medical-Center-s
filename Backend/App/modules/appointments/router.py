"""MED V2 — Appointments router. Kept thin: HTTP only, logic lives in service."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentRequestCreate,
    AppointmentRequestRead,
)
from App.modules.appointments.service import AppointmentService, NotFoundError, ValidationError

router = APIRouter(prefix="/appointments", tags=["appointments"])


def get_service(db: Session = Depends(get_db)) -> AppointmentService:
    return AppointmentService(db, now=datetime.now(timezone.utc))


# -- Requests --------------------------------------------------------------
@router.post(
    "/requests",
    response_model=AppointmentRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar solicitação de consulta",
)
def create_request(payload: AppointmentRequestCreate, service: AppointmentService = Depends(get_service)):
    try:
        return service.create_request(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/requests/patient/{patient_id}",
    response_model=list[AppointmentRequestRead],
    summary="Listar solicitações de um paciente",
)
def list_requests(patient_id: int, service: AppointmentService = Depends(get_service)):
    try:
        return service.list_requests_by_patient(patient_id)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# -- Appointments ----------------------------------------------------------
@router.post(
    "",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar consulta a partir de uma solicitação",
)
def create_appointment(payload: AppointmentCreate, service: AppointmentService = Depends(get_service)):
    try:
        return service.create_appointment(payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/patient/{patient_id}",
    response_model=list[AppointmentRead],
    summary="Listar consultas de um paciente",
)
def list_appointments(patient_id: int, service: AppointmentService = Depends(get_service)):
    try:
        return service.list_appointments_by_patient(patient_id)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/{appointment_id}",
    response_model=AppointmentRead,
    summary="Detalhar uma consulta",
)
def get_appointment(appointment_id: int, service: AppointmentService = Depends(get_service)):
    try:
        return service.get_appointment(appointment_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
