from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampedRead(APIModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
