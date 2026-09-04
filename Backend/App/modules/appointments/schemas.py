"""MED V2 — API schemas (contract) for appointments and scheduling."""

import enum
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------
class AppointmentRequestCreate(BaseModel):
    """Payload to create an appointment request."""

    patient_id: int = Field(gt=0, description="ID do paciente")
    specialty: str = Field(min_length=2, max_length=100, description="Especialidade desejada")
    preferred_date: date = Field(description="Data preferencial")
    preferred_time: time = Field(description="Horário preferencial")
    reason: str = Field(default="", max_length=500, description="Motivo da consulta")


class AppointmentRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    specialty: str
    preferred_date: date
    preferred_time: time
    reason: str
    status: enum.Enum  # RequestStatus
    created_at: datetime


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------
class AppointmentCreate(BaseModel):
    """Payload to schedule an appointment from an existing request."""

    request_id: int = Field(gt=0, description="ID da solicitação relacionada")
    doctor_name: str = Field(min_length=2, max_length=150, description="Nome do médico")
    hospital_name: str = Field(min_length=2, max_length=150, description="Nome do hospital")
    scheduled_at: datetime = Field(description="Data e hora da consulta")
    notes: str = Field(default="", max_length=500, description="Observações")


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    patient_id: int
    specialty: str
    doctor_name: str
    hospital_name: str
    scheduled_at: datetime
    status: enum.Enum  # AppointmentStatus
    notes: str
    created_at: datetime
