"""MED V3 — Data access layer for care requests (no business rules here)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.care_requests.models import CareRequest
from App.modules.users.models import User


class CareRequestRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- CareRequest -------------------------------------------------------
    def create(self, care_request: CareRequest) -> CareRequest:
        self.db.add(care_request)
        self.db.commit()
        self.db.refresh(care_request)
        return care_request

    def get(self, request_id: int) -> CareRequest | None:
        return self.db.get(CareRequest, request_id)

    def list_by_patient(self, patient_id: int) -> list[CareRequest]:
        stmt = (
            select(CareRequest)
            .where(CareRequest.patient_id == patient_id)
            .order_by(CareRequest.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    # -- Users (validation support) -----------------------------------------
    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)
