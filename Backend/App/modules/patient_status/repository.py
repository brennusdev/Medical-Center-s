"""MED V5 — Data access layer for patient status updates (no business rules here)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.care_requests.models import CareRequest
from App.modules.patient_status.models import PatientStatusUpdate
from App.modules.users.models import User


class PatientStatusRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, update: PatientStatusUpdate) -> PatientStatusUpdate:
        self.db.add(update)
        self.db.commit()
        self.db.refresh(update)
        return update

    def get(self, status_id: int) -> PatientStatusUpdate | None:
        return self.db.get(PatientStatusUpdate, status_id)

    def list_by_patient(self, patient_id: int) -> list[PatientStatusUpdate]:
        stmt = (
            select(PatientStatusUpdate)
            .where(PatientStatusUpdate.patient_id == patient_id)
            .order_by(PatientStatusUpdate.created_at.desc(), PatientStatusUpdate.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_care_request(self, care_request_id: int) -> list[PatientStatusUpdate]:
        stmt = (
            select(PatientStatusUpdate)
            .where(PatientStatusUpdate.care_request_id == care_request_id)
            .order_by(PatientStatusUpdate.created_at.asc(), PatientStatusUpdate.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    # -- Suporte a validações do service --------------------------------------
    def get_care_request(self, care_request_id: int) -> CareRequest | None:
        return self.db.get(CareRequest, care_request_id)

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)
