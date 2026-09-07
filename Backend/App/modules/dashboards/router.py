"""MED V8 — Router dos Dashboards.

Endpoints por contexto (como especificado na V8):
- GET /dashboard/patient/{patient_id}
- GET /dashboard/doctor/{doctor_id}
- GET /dashboard/hospital/{hospital_id}
- GET /dashboard/admin

Em V9 estes endpoints passam por autenticação + ownership (o paciente só vê o
próprio dashboard). A forma da resposta não muda, para não quebrar o frontend.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from App.core.database import get_db
from App.modules.dashboards.schemas import (
    AdminDashboardOut,
    DoctorDashboardOut,
    HospitalDashboardOut,
    PatientDashboardOut,
)
from App.modules.dashboards.service import DashboardService, NotFoundError

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


@router.get("/patient/{patient_id}", response_model=PatientDashboardOut, summary="Dashboard do paciente")
def patient_dashboard(patient_id: int, service: DashboardService = Depends(get_service)):
    try:
        return service.patient_dashboard(patient_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/doctor/{doctor_id}", response_model=DoctorDashboardOut, summary="Dashboard do médico/profissional")
def doctor_dashboard(doctor_id: int, service: DashboardService = Depends(get_service)):
    try:
        return service.doctor_dashboard(doctor_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/hospital/{hospital_id}", response_model=HospitalDashboardOut, summary="Dashboard do hospital")
def hospital_dashboard(hospital_id: int, service: DashboardService = Depends(get_service)):
    try:
        return service.hospital_dashboard(hospital_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/admin", response_model=AdminDashboardOut, summary="Dashboard administrativo")
def admin_dashboard(service: DashboardService = Depends(get_service)):
    # Sem parâmetros: visão global. Acesso restrito chega na V9 (RBAC).
    return service.admin_dashboard()
