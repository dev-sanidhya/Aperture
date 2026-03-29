from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    AIRunJobType,
    BusinessState,
    CampaignChannel,
    CampaignStatus,
    ChannelType,
    ProviderHealth,
    ReplyIntent,
    SendEligibility,
    ServiceLane,
)


class BusinessCreate(BaseModel):
    name: str
    city: str | None = None
    category: str | None = None
    subcategory: str | None = None
    google_place_id: str | None = None


class PlacesIngestRequest(BaseModel):
    text_query: str
    page_size: int = 10


class PlacesIngestResponse(BaseModel):
    imported: int
    updated: int
    total_places: int


class PlacesMatrixRequest(BaseModel):
    cities: list[str]
    categories: list[str]
    page_size: int = 10


class PlacesMatrixResponse(BaseModel):
    queries_run: int
    imported: int
    updated: int
    total_places: int


class BusinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str | None
    category: str | None
    subcategory: str | None
    google_place_id: str | None
    state: BusinessState
    priority_score: float


class LeadSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: UUID
    state: BusinessState
    service_lane: ServiceLane
    routing_channel: ChannelType
    routing_tier: str
    rationale: str | None


class CampaignCreate(BaseModel):
    name: str
    channel: CampaignChannel
    template_version: str
    daily_cap: int
    filters: dict = {}


class CampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    channel: CampaignChannel
    status: CampaignStatus
    template_version: str
    daily_cap: int
    filters: dict


class ProviderStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider_name: str
    health: ProviderHealth
    default_model: str | None
    last_probe_at: datetime | None
    last_error: str | None
    status_payload: dict


class ContactPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    channel: ChannelType
    value: str
    confidence: float
    whatsapp_likely: bool
    send_eligibility: SendEligibility


class AIRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_name: str
    model_alias: str
    job_type: AIRunJobType
    status: str
    duration_ms: int | None
    output_json: dict
    error_text: str | None


class ReplyEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    intent: ReplyIntent
    normalized_text: str | None
    recommended_action: str | None
