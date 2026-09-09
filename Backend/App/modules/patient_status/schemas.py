"""MED V5 — API schemas (contract) for patient status updates."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from App.modules.patient_status.models import PatientState


class PatientStatusUpdateCreate(BaseModel):
    """Payload para criar uma atualização de estado.

    Todos os campos são relatos do próprio paciente; o sistema apenas os
    registra (severity é uma escala subjetiva 0-10, sem interpretação clínica).
    """

    patient_id: int = Field(gt=0, description="ID do paciente (deve ser o dono da solicitação)")
    care_request_id: int = Field(gt=0, description="ID da CareRequest relacionada")
    state: PatientState = Field(description="Estado relatado: IMPROVED / STABLE / WORSENED")
    symptoms: str = Field(default="", max_length=2000, description="Sintomas relatados pelo paciente")
    severity: int = Field(ge=0, le=10, description="Intensidade percebida (0-10, subjetiva)")
    description: str = Field(default="", max_length=2000, description="Descrição da situação")
    notes: str = Field(default="", max_length=500, description="Observações")


class PatientStatusUpdateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    care_request_id: int
    state: PatientState
    symptoms: str
    severity: int
    description: str
    notes: str
    created_at: datetime
