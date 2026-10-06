from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class IncidentCreate(BaseModel):
    title: str = Field(min_length=4, max_length=200); service: str = Field(pattern=r"^[a-z0-9-]+$")
    environment: Literal["staging", "production"]; severity: Literal["SEV1", "SEV2", "SEV3", "SEV4"]
    scenario: Literal["bad_deployment", "db_exhaustion", "dependency_outage", "prompt_injection"] = "bad_deployment"
class ApprovalRequest(BaseModel):
    decision: Literal["approved", "rejected"]; approver: str = Field(min_length=2, max_length=100); comment: str | None = Field(default=None, max_length=500)
class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; title: str; service: str; environment: str; severity: str; scenario: str; status: str
    hypothesis: str | None; confidence: float | None; recommendation: str | None; proposed_action: dict | None
    tool_call_count: int; accumulated_cost: float; created_at: datetime; updated_at: datetime
class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; sequence: int; event_type: str; actor: str; state_before: str | None; state_after: str | None; payload: dict; created_at: datetime
