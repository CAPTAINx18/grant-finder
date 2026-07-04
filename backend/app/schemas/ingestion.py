from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel


class SourceResponse(BaseModel):
    id: UUID
    name: str
    url: str
    update_method: str
    cron_schedule: str
    is_active: bool
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_error: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TriggerResponse(BaseModel):
    message: str
    task_id: str


class StatusResponse(BaseModel):
    source_id: UUID
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_error: Optional[str] = None
