"""MED V6 — API schemas (contract) for medical evaluations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicalEvaluationCreate(BaseModel):
    """Payload para criar uma avaliação profissional.

    O texto é registrado literalmente pelo profissional autorizado; o sistema
    não o gera, não o interpreta e não o transforma em diagnóstico automático.
    """

    professional_id: int = Field(gt=0, description="ID do profissional responsável")
    patient_status_update_id: int = Field(gt=0, description="Atualização de estado avaliada")
    care_request_id: int = Field(gt=0, description="Solicitação de atendimento relacionada")
    evaluation: str = Field(min_length=2, max_length=2000, description="Avaliação profissional")
    recommendation: str = Field(default="", max_length=500, description="Recomendação")
    queue_id: int | None = Field(default=None, gt=0, description="Fila relacionada (opcional)")


class MedicalEvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    professional_id: int
    patient_status_update_id: int
    care_request_id: int
    evaluation: str
    recommendation: str
    queue_id: int | None
    created_at: datetime
