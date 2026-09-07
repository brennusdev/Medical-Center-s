"""MED V6 — Data access layer for medical evaluations (no business rules here)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.care_requests.models import CareRequest
from App.modules.medical_evaluations.models import MedicalEvaluation
from App.modules.patient_status.models import PatientStatusUpdate
from App.modules.users.models import User


class MedicalEvaluationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, evaluation: MedicalEvaluation) -> MedicalEvaluation:
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def get(self, evaluation_id: int) -> MedicalEvaluation | None:
        return self.db.get(MedicalEvaluation, evaluation_id)

    def list_by_care_request(self, care_request_id: int) -> list[MedicalEvaluation]:
        stmt = (
            select(MedicalEvaluation)
            .where(MedicalEvaluation.care_request_id == care_request_id)
            .order_by(MedicalEvaluation.created_at.asc(), MedicalEvaluation.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_professional(self, professional_id: int) -> list[MedicalEvaluation]:
        stmt = (
            select(MedicalEvaluation)
            .where(MedicalEvaluation.professional_id == professional_id)
            .order_by(MedicalEvaluation.created_at.desc(), MedicalEvaluation.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    # -- Suporte a validações do service --------------------------------------
    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_status_update(self, status_update_id: int) -> PatientStatusUpdate | None:
        return self.db.get(PatientStatusUpdate, status_update_id)

    def get_care_request(self, care_request_id: int) -> CareRequest | None:
        return self.db.get(CareRequest, care_request_id)
