"""MED V15 — Schemas (contrato) do módulo intelligence."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SpecialtyLoad(BaseModel):
    """Carga operacional de uma especialidade (descritivo, não clínico)."""

    specialty: str
    open_queues: int = Field(ge=0, description="Entradas abertas na fila (WAITING/IN_REVIEW)")
    urgent_count: int = Field(ge=0, description="Quantas ativas estão marcadas URGENT (por humano)")
    level: str = Field(description="LOW | MEDIUM | HIGH — heurística explícita, não diagnóstico")


class WaitTimeInsight(BaseModel):
    """Tempo médio observado entre entrar na fila e sair (por especialidade)."""

    specialty: str
    average_wait_hours: float | None = None
    samples: int = Field(ge=0)


class AttentionSignal(BaseModel):
    """Sinal INFORMATIVO de atenção para revisão humana.

    Critério totalmente explícito: pior estado reportado = WORSENED e
    permanência na fila acima do limiar. Nada é alterado automaticamente.
    """

    model_config = ConfigDict(from_attributes=True)

    queue_id: int
    patient_id: int
    care_request_id: int
    specialty: str
    priority: str
    position: int
    hours_waiting: float
    last_state: str
    reason: str = Field(description="Explicação legível da heurística que gerou o sinal")
    created_at: datetime | None = None


class IntelligenceSummary(BaseModel):
    """Resposta agregada do endpoint /intelligence/summary."""

    generated_at: datetime
    loads: list[SpecialtyLoad]
    wait_times: list[WaitTimeInsight]
    attention_signals: list[AttentionSignal]
