"""MED V3 — API schemas (contract) for care requests."""

import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CareRequestCreate(BaseModel):
    """Payload para criar uma solicitação de atendimento.

    Todos os campos clínicos são relatos informados pelo paciente;
    o sistema apenas os registra, sem interpretar/diagnosticar.
    """

    patient_id: int = Field(gt=0, description="ID do paciente")
    reason: str = Field(min_length=2, max_length=500, description="Motivo da solicitação")
    specialty: str = Field(min_length=2, max_length=100, description="Especialidade desejada")
    symptoms: str = Field(default="", max_length=2000, description="Sintomas relatados pelo paciente")
    description: str = Field(default="", max_length=2000, description="Descrição da situação")
    cep: str = Field(min_length=8, max_length=9, description="CEP de localização")
    referral: str = Field(default="", max_length=500, description="Encaminhamento médico, quando disponível")
    discomfort_level: int = Field(ge=1, le=10, description="Nível de desconforto informado (1-10)")
    symptom_onset: date = Field(description="Data de início dos sintomas")
    notes: str = Field(default="", max_length=500, description="Observações")


class CareRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    reason: str
    specialty: str
    symptoms: str
    description: str
    cep: str
    referral: str
    discomfort_level: int
    symptom_onset: date
    notes: str
    status: enum.Enum  # CareRequestStatus
    created_at: datetime
