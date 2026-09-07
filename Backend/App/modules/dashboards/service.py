"""MED V8 — Serviço dos Dashboards.

Monta cada visão a partir dos REPOSITÓRIOS dos domínios existentes + o
repositório de analytics. Nenhuma regra de negócio nova é criada aqui:
o dashboard apenas lê e organiza. Isso cumpre a regra "não duplicar lógica".

Casos vazios (sem atendimento/consulta/fila) são respostas válidas com listas
vazias e campos None — nunca erro.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.analytics.repository import AnalyticsRepository, ACTIVE_QUEUE_STATUSES, OPEN_CARE_STATUSES
from App.modules.analytics.service import AnalyticsService
from App.modules.appointments.models import Appointment, AppointmentStatus
from App.modules.care_requests.models import CareRequest
from App.modules.notifications.models import Notification
from App.modules.queues.models import Queue
from App.modules.users.models import User


class NotFoundError(Exception):
    """Entidade não encontrada (404 no transporte)."""


class _SharedReads:
    """Consultas compartilhadas pelos dashboards (SQLAlchemy ORM simples).

    Consultas de dashboards são leituras de "telas": limitadas e ordenadas —
    diferente do analytics, aqui carregamos poucas linhas (LIMIT) porque a
    tela precisa dos objetos completos, não apenas de contagens.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def next_appointment(self, patient_id: int) -> Appointment | None:
        stmt = (
            select(Appointment)
            .where(
                Appointment.patient_id == patient_id,
                Appointment.scheduled_at >= datetime.now(timezone.utc),
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.scheduled_at.asc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def open_care_requests(self, patient_id: int, limit: int = 10) -> list[CareRequest]:
        stmt = (
            select(CareRequest)
            .where(CareRequest.patient_id == patient_id, CareRequest.status.in_(OPEN_CARE_STATUSES))
            .order_by(CareRequest.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def care_requests(self, care_request_ids: list[int]) -> list[CareRequest]:
        if not care_request_ids:
            return []
        stmt = select(CareRequest).where(CareRequest.id.in_(care_request_ids))
        return list(self.db.scalars(stmt).all())

    def queues_by_care_requests(self, care_request_ids: list[int]) -> list[Queue]:
        if not care_request_ids:
            return []
        stmt = (
            select(Queue)
            .where(Queue.care_request_id.in_(care_request_ids), Queue.status.in_(ACTIVE_QUEUE_STATUSES))
            .order_by(Queue.position.asc())
        )
        return list(self.db.scalars(stmt).all())

    def notifications(self, user_id: int, limit: int = 10) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def unread_count(self, user_id: int) -> int:
        from sqlalchemy import func

        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.read.is_(False)
        )
        return int(self.db.scalar(stmt) or 0)


# Traduções de apresentação (somente texto; nenhuma decisão clínica).
_NEXT_STEP_BY_STATUS = {
    "CREATED": "Sua solicitação foi recebida e aguarda triagem.",
    "IN_REVIEW": "Sua solicitação está em avaliação pela equipe.",
    "REFERRED": "Você foi encaminhado(a) — acompanhe sua fila.",
    "SCHEDULED": "Você possui consulta agendada.",
    "CANCELLED": "Sua solicitação foi cancelada.",
    "COMPLETED": "Seu atendimento foi concluído.",
}


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.shared = _SharedReads(db)
        self.analytics_repo = AnalyticsRepository(db)
        self.analytics = AnalyticsService(db)

    # -- Paciente ---------------------------------------------------------------
    def patient_dashboard(self, patient_id: int) -> dict:
        user = self.shared.get_user(patient_id)
        if user is None:
            raise NotFoundError(f"Paciente {patient_id} não encontrado")

        open_requests = self.shared.open_care_requests(patient_id)
        queues = self.shared.queues_by_care_requests([r.id for r in open_requests])
        next_appt = self.shared.next_appointment(patient_id)
        latest_status = self.analytics_repo.patient_latest_status_update(patient_id)
        notifications = self.shared.notifications(patient_id)

        # "Próximo passo" deriva do status da solicitação mais recente aberta
        # (ou da existência de consulta agendada) — apenas apresentação.
        if next_appt is not None:
            next_step = "Você possui consulta agendada."
        elif open_requests:
            next_step = _NEXT_STEP_BY_STATUS.get(open_requests[0].status.value, "Aguarde atualizações.")
        else:
            next_step = "Nenhum atendimento em andamento."

        return {
            "patient_id": patient_id,
            "full_name": user.full_name,
            "next_appointment": next_appt,
            "next_step": next_step,
            "open_care_requests": open_requests,
            "queues": queues,
            "latest_status": latest_status,
            "notifications": notifications,
            "unread_notifications": self.shared.unread_count(patient_id),
        }

    # -- Médico ---------------------------------------------------------------
    def doctor_dashboard(self, doctor_id: int) -> dict:
        user = self.shared.get_user(doctor_id)
        if user is None:
            raise NotFoundError(f"Profissional {doctor_id} não encontrado")

        received = self.analytics_repo.doctor_recent_care_requests()
        # "Casos aguardando avaliação": última atualização de estado de cada
        # solicitação aberta recente. LIMIT pequeno (tela), evita varrer a tabela.
        awaiting: list = []
        for cr in received[:10]:
            latest = self.analytics_repo.patient_latest_status_update_by_request(cr.id)
            if latest is not None:
                awaiting.append(latest)
        # Consultas do dia (janela [hoje 00:00, amanhã 00:00)).
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        today_appointments = list(
            self.db.scalars(
                select(Appointment)
                .where(
                    Appointment.scheduled_at >= day_start,
                    Appointment.scheduled_at < day_end,
                    Appointment.status != AppointmentStatus.CANCELLED,
                )
                .order_by(Appointment.scheduled_at.asc())
            ).all()
        )

        active_queues = list(
            self.db.scalars(
                select(Queue)
                .where(Queue.status.in_(ACTIVE_QUEUE_STATUSES))
                .order_by(Queue.specialty.asc(), Queue.position.asc())
                .limit(50)
            ).all()
        )

        return {
            "doctor_id": doctor_id,
            "full_name": user.full_name,
            "received_requests": received,
            "awaiting_evaluation": awaiting,
            "today_appointments": today_appointments,
            "active_queues": active_queues,
            "notifications": self.shared.notifications(doctor_id),
        }

    # -- Hospital ---------------------------------------------------------------
    def hospital_dashboard(self, hospital_id: int) -> dict:
        if hospital_id <= 0:
            raise NotFoundError("hospital_id inválido")
        open_queues = self.analytics_repo.hospital_open_queues(hospital_id)
        counts = self.analytics_repo.hospital_counts(hospital_id, None, None)

        # Distribuição operacional: agrupamento em Python sobre uma lista já
        # LIMITADA às filas ativas do hospital — o volume por hospital é
        # pequeno e precisamos dos grupos com detalhe (waiting/posição).
        by_specialty: dict[str, dict] = {}
        for q in open_queues:
            entry = by_specialty.setdefault(
                q.specialty, {"specialty": q.specialty, "total_active": 0, "waiting": 0, "next_position": 0}
            )
            entry["total_active"] += 1
            if q.status == "WAITING":
                entry["waiting"] += 1
                entry["next_position"] = max(entry["next_position"], q.position)

        return {
            "hospital_id": hospital_id,
            "open_queues": open_queues,
            "by_specialty": sorted(by_specialty.values(), key=lambda e: -e["total_active"]),
            "open_queues_count": counts["open_queues"],
            "waiting_count": counts["waiting"],
            "completed_count": counts["completed"],
        }

    # -- Admin ---------------------------------------------------------------
    def admin_dashboard(self) -> dict:
        """Números de gestão via AnalyticsService (mesma fonte dos endpoints
        de analytics — nunca dois cálculos diferentes para o mesmo número)."""
        overview = self.analytics.overview(AnalyticsFiltersEmpty())
        return {
            "generated_at": datetime.now(timezone.utc),
            "total_care_requests": overview["total_care_requests"],
            "open_care_requests": overview["open_care_requests"],
            "total_appointments": overview["total_appointments"],
            "waiting_queue_entries": overview["waiting_queue_entries"],
            "average_wait_hours": self.analytics.wait_times(AnalyticsFiltersEmpty())["average_wait_hours"],
            "by_specialty": self.analytics_repo.by_specialty(None, None, None),
            "by_hospital": self.analytics_repo.by_hospital(None, None, None),
        }


class AnalyticsFiltersEmpty:
    """Filtros vazios (sem janela/especialidade/hospital) para visão global.

    Usa duck typing compatível com AnalyticsFilters — basta ao service chamar
    validate_window(), que aqui não precisa validar nada.
    """

    start_date = None
    end_date = None
    specialty = None
    hospital_id = None

    def validate_window(self) -> None:  # noqa: D102 — nada a validar
        return None
