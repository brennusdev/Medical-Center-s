"""MED V8 — Schemas de saída dos dashboards.

Contratos separados por perfil: cada dashboard devolve APENAS o que aquele
perfil precisa e pode ver (menor superfície de dados = menor risco em V9).
"""

from datetime import date, datetime

from pydantic import BaseModel
from App.modules.analytics.schemas import GroupCount


class NextAppointmentOut(BaseModel):
    """Consulta futura mais próxima (resumo amigável)."""

    id: int
    specialty: str
    doctor_name: str
    hospital_name: str
    scheduled_at: datetime
    status: str


class QueueOut(BaseModel):
    """Entrada de fila com os campos do exemplo conceitual (prioridade/posição)."""

    id: int
    specialty: str
    status: str
    priority: str
    position: int
    hospital_id: int | None
    entered_at: datetime
    updated_at: datetime


class CareRequestOut(BaseModel):
    """Resumo de solicitação de atendimento (sem dados clínicos extensos)."""

    id: int
    specialty: str
    reason: str
    status: str
    created_at: datetime


class LatestStatusOut(BaseModel):
    """Última atualização do paciente ('Estou me sentindo melhor.')."""

    id: int
    care_request_id: int
    state: str
    severity: int
    description: str
    created_at: datetime


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime


class PatientDashboardOut(BaseModel):
    """Resposta do GET /dashboard/patient/{patient_id}.

    `next_step` é um texto orientado ao paciente derivado do status ATUAL —
    tradução de apresentação, não regra de negócio (não altera dados).
    """

    patient_id: int
    full_name: str
    next_appointment: NextAppointmentOut | None
    next_step: str
    open_care_requests: list[CareRequestOut]
    queues: list[QueueOut]
    latest_status: LatestStatusOut | None
    notifications: list[NotificationOut]
    unread_notifications: int


class DoctorDashboardOut(BaseModel):
    """Resposta do GET /dashboard/doctor/{doctor_id}.

    Mostra apenas contexto profissional (casos/filas/consultas do dia).
    NÃO expõe dados que o profissional não solicitou — a profundidade
    (relatos completos) continua exigindo acesso explícito por solicitação.
    """

    doctor_id: int
    full_name: str
    received_requests: list[CareRequestOut]
    awaiting_evaluation: list[LatestStatusOut]
    today_appointments: list[NextAppointmentOut]
    active_queues: list[QueueOut]
    notifications: list[NotificationOut]


class SpecialtyLoadOut(BaseModel):
    """Carga operacional de uma especialidade dentro do hospital."""

    specialty: str
    total_active: int
    waiting: int
    next_position: int


class HospitalDashboardOut(BaseModel):
    """Resposta do GET /dashboard/hospital/{hospital_id}."""

    hospital_id: int
    open_queues: list[QueueOut]
    by_specialty: list[SpecialtyLoadOut]
    open_queues_count: int
    waiting_count: int
    completed_count: int


class AdminDashboardOut(BaseModel):
    """Resposta do GET /dashboard/admin — somente gestão, sem dados clínicos."""

    generated_at: datetime
    total_care_requests: int
    open_care_requests: int
    total_appointments: int
    waiting_queue_entries: int
    average_wait_hours: float | None
    # Reuso do contrato de linha de distribuição do analytics (sem duplicar schema).
    by_specialty: list[GroupCount]
    by_hospital: list[GroupCount]
