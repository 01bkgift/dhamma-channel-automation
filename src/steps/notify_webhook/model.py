from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class NotifyTarget(BaseModel):
    name: str
    url: str

class TargetResult(BaseModel):
    name: str
    url_redacted: str
    result: Literal["success", "error", "timeout"]
    http_status: Optional[int] = None

class NotifySummary(BaseModel):
    schema_version: str = "v1"
    run_id: str
    timestamp_utc: str
    notification_status: Literal["sent", "failed", "skipped"]
    targets_attempted: List[TargetResult] = Field(default_factory=list)
    message_digest: str
    reason_codes: List[str] = Field(default_factory=list)
