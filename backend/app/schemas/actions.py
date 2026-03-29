from __future__ import annotations

from pydantic import BaseModel


class BusinessActionRequest(BaseModel):
    business_id: str


class DraftSendRequest(BaseModel):
    draft_message_id: str
    approve: bool = True


class EnrichmentResponse(BaseModel):
    sources_added: int
    contacts_added: int
    websites_added: int


class PipelineRunResponse(BaseModel):
    sources_added: int
    contacts_added: int
    websites_added: int
    score: float
    evidence_pack_id: str
