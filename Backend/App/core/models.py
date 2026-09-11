#
# ÁREA: REGISTRO CENTRAL DE MODELS (core/models.py)
# Responsabilidade: importar TODOS os models ORM de todos os módulos em um
# único lugar. O Alembic (migrations) importa este arquivo, então qualquer
# model novo PRECISA estar listado aqui ou não gera migration.
# `# noqa: F401` = imports apenas por efeito colateral (registro nas tabelas).
#
"""Central model registry — imported by Alembic so migrations see all tables."""

from App.core.database import Base  # noqa: F401
from App.modules.appointments.models import (  # noqa: F401
    Appointment,
    AppointmentRequest,
    AppointmentStatus,
    RequestStatus,
)

# MED V10 — auditoria (append-only).
from App.modules.audit.models import AuditAction, AuditLog  # noqa: F401
from App.modules.care_requests.models import (  # noqa: F401
    CareRequest,
    CareRequestStatus,
)
from App.modules.medical_evaluations.models import MedicalEvaluation  # noqa: F401
from App.modules.patient_status.models import (  # noqa: F401
    PatientState,
    PatientStatusUpdate,
)
from App.modules.queues.models import (  # noqa: F401
    Queue,
    QueueEvent,
    QueueEventType,
    QueuePriority,
    QueueStatus,
)
from App.modules.users.models import User  # noqa: F401

# ÁREA: LISTA DE EXPORTAÇÃO — espelha os imports acima; usado por
# `from App.core.models import *` e por inspeção (CI checa completude).
__all__ = [
    "Base",
    "CareRequest",
    "CareRequestStatus",
    "Appointment",
    "AppointmentRequest",
    "AppointmentStatus",
    "RequestStatus",
    "Queue",
    "QueueEvent",
    "QueueEventType",
    "QueuePriority",
    "QueueStatus",
    "PatientState",
    "PatientStatusUpdate",
    "MedicalEvaluation",
    "User",
    "AuditLog",
    "AuditAction",
]
