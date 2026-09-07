"""MED V8 — Contratos Pydantic do domínio de Analytics.

Os schemas de saída descrevem exatamente o que cada endpoint devolve, para que
o frontend e o mobile dependam de um contrato estável (e não de dicts soltos).
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from App.modules.queues.models import QueuePriority, QueueStatus


class AnalyticsFilters(BaseModel):
    """Filtros comuns de período/especialidade/hospital.

    Regra: quando `start_date > end_date`, a janela é inválida e devemos falhar
    cedo (422) — evita consultas inúteis ao banco e respostas enganosas.
    """

    start_date: date | None = None
    end_date: date | None = None
    specialty: str | None = None
    hospital_id: int | None = None

    @field_validator("specialty")
    @classmethod
    def _clean_specialty(cls, v: str | None) -> str | None:
        # Normalização simples: espaços em branco não são parte da especialidade.
        return v.strip() if v else v

    @field_validator("hospital_id")
    @classmethod
    def _positive_hospital(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("hospital_id deve ser um inteiro positivo")
        return v

    def validate_window(self) -> None:
        """Validação de janela temporal (chamada no service, não no transporte)."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date não pode ser maior que end_date")


class CountMetric(BaseModel):
    """Contagem agregada simples (ex.: total de solicitações)."""

    total: int


class OverviewMetrics(BaseModel):
    """Painel geral de volumes — alimenta o dashboard administrativo.

    Decisão: números derivados de COUNT SQL, nunca de listas carregadas
    inteiras em memória (performance V8).
    """

    total_care_requests: int
    open_care_requests: int
    total_appointments: int
    total_queue_entries: int
    waiting_queue_entries: int
    pending_procedures: int


class GroupCount(BaseModel):
    """Uma linha de distribuição (GROUP BY) — especialidade ou hospital."""

    key: str
    total: int
    open: int = 0


class PriorityDistribution(BaseModel):
    """Distribuição das prioridades operacionais (V4) ativas na fila."""

    priority: QueuePriority
    total: int


class QueueStatusDistribution(BaseModel):
    """Distribuição de status das entradas de fila (diagnóstico operacional)."""

    status: QueueStatus
    total: int


class WaitTimeMetric(BaseModel):
    """Tempo médio de espera (em horas, com 2 casas).

    Definição de negócio: diferença entre `entered_at` (entrada na fila) e
    `updated_at` (última mudança) das entradas COMPLETED/REMOVED — ou seja,
    apenas esperas já encerradas contam para a média. Entradas ainda ativas
    seriam uma projeção, não um dado medido.
    """

    average_wait_hours: float | None
    samples: int


class AppointmentPeriodMetric(BaseModel):
    """Consultas agregadas por dia (GROUP BY date(scheduled_at))."""

    day: date
    total: int


class AnalyticsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
