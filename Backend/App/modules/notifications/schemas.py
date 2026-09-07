"""MED V7 — API schemas for notifications."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    title: str
    message: str
    read: bool
    related_resource_type: str | None
    related_resource_id: int | None
    created_at: datetime
