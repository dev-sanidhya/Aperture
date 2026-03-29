from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    AIRunJobType,
    AIRunStatus,
    BusinessState,
    CampaignChannel,
    CampaignStatus,
    ChannelType,
    MessageDirection,
    ProviderHealth,
    ProviderKind,
    ReplyIntent,
    SendEligibility,
    ServiceLane,
    SourceType,
    SuppressionReason,
    VerificationStatus,
)
from app.models.base import Base, TimestampMixin, UUIDMixin


class Business(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    google_place_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    normalized_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    normalized_phone: Mapped[str | None] = mapped_column(String(64), index=True)
    state: Mapped[BusinessState] = mapped_column(Enum(BusinessState), default=BusinessState.NO_WEBSITE, nullable=False)
    city: Mapped[str | None] = mapped_column(String(128))
    category: Mapped[str | None] = mapped_column(String(128))
    subcategory: Mapped[str | None] = mapped_column(String(128))
    priority_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    locations = relationship("BusinessLocation", back_populates="business", cascade="all, delete-orphan")
    sources = relationship("SourceRecord", back_populates="business", cascade="all, delete-orphan")
    websites = relationship("Website", back_populates="business", cascade="all, delete-orphan")
    contacts = relationship("ContactPoint", back_populates="business", cascade="all, delete-orphan")
    segment = relationship("LeadSegment", back_populates="business", uselist=False, cascade="all, delete-orphan")


class BusinessLocation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "business_locations"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    address: Mapped[str | None] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(128), index=True)
    area: Mapped[str | None] = mapped_column(String(128))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    business = relationship("Business", back_populates="locations")


class SourceRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "source_records"

    business_id: Mapped[str | None] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    parser_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)

    business = relationship("Business", back_populates="sources")


class Website(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "websites"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    normalized_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    crawl_state: Mapped[str] = mapped_column(String(64), default="pending", nullable=False)
    is_weak: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    audit_summary: Mapped[str | None] = mapped_column(Text)

    business = relationship("Business", back_populates="websites")


class ContactPoint(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contact_points"
    __table_args__ = (UniqueConstraint("business_id", "channel", "value", name="uq_contact_points_business_channel_value"),)

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    public_business_contact: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    whatsapp_likely: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    send_eligibility: Mapped[SendEligibility] = mapped_column(
        Enum(SendEligibility), default=SendEligibility.HOLD, nullable=False
    )

    business = relationship("Business", back_populates="contacts")


class LeadSegment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lead_segments"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    state: Mapped[BusinessState] = mapped_column(Enum(BusinessState), nullable=False)
    service_lane: Mapped[ServiceLane] = mapped_column(Enum(ServiceLane), nullable=False)
    routing_channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), nullable=False)
    routing_tier: Mapped[str] = mapped_column(String(64), default="normal", nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)

    business = relationship("Business", back_populates="segment")


class EvidencePack(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "evidence_packs"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    observed_issue: Mapped[str] = mapped_column(Text, nullable=False)
    consequence: Mapped[str] = mapped_column(Text, nullable=False)
    offer_match: Mapped[ServiceLane] = mapped_column(Enum(ServiceLane), nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class OpportunityScore(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "opportunity_scores"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Campaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[CampaignChannel] = mapped_column(Enum(CampaignChannel), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    template_version: Mapped[str] = mapped_column(String(64), nullable=False)
    daily_cap: Mapped[int] = mapped_column(Integer, nullable=False)
    filters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class CampaignMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaign_members"
    __table_args__ = (UniqueConstraint("campaign_id", "business_id", name="uq_campaign_members_campaign_business"),)

    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    sequence_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state: Mapped[str] = mapped_column(String(64), default="queued", nullable=False)
    next_due_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    last_sent_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    last_reply_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))


class MessageTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "message_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[CampaignChannel] = mapped_column(Enum(CampaignChannel), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class AIRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_runs"

    business_id: Mapped[str | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"))
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_alias: Mapped[str] = mapped_column(String(128), nullable=False)
    job_type: Mapped[AIRunJobType] = mapped_column(Enum(AIRunJobType), nullable=False)
    status: Mapped[AIRunStatus] = mapped_column(Enum(AIRunStatus), default=AIRunStatus.PENDING, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    output_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_text: Mapped[str | None] = mapped_column(Text)


class DraftMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "draft_messages"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    evidence_pack_id: Mapped[str] = mapped_column(ForeignKey("evidence_packs.id", ondelete="CASCADE"), nullable=False)
    ai_run_id: Mapped[str | None] = mapped_column(ForeignKey("ai_runs.id", ondelete="SET NULL"))
    channel: Mapped[CampaignChannel] = mapped_column(Enum(CampaignChannel), nullable=False)
    sequence_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    template_version: Mapped[str] = mapped_column(String(64), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SendAttempt(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "send_attempts"

    draft_message_id: Mapped[str | None] = mapped_column(ForeignKey("draft_messages.id", ondelete="SET NULL"))
    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(Enum(MessageDirection), nullable=False)
    provider_kind: Mapped[ProviderKind] = mapped_column(Enum(ProviderKind), nullable=False)
    channel: Mapped[CampaignChannel] = mapped_column(Enum(CampaignChannel), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64), default="queued", nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)


class ReplyEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reply_events"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    send_attempt_id: Mapped[str | None] = mapped_column(ForeignKey("send_attempts.id", ondelete="SET NULL"))
    provider_kind: Mapped[ProviderKind] = mapped_column(Enum(ProviderKind), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    intent: Mapped[ReplyIntent] = mapped_column(Enum(ReplyIntent), default=ReplyIntent.UNKNOWN, nullable=False)
    recommended_action: Mapped[str | None] = mapped_column(Text)


class SuppressionEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "suppression_entries"

    business_id: Mapped[str | None] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    channel: Mapped[ChannelType | None] = mapped_column(Enum(ChannelType))
    reason: Mapped[SuppressionReason] = mapped_column(Enum(SuppressionReason), nullable=False)
    expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))


class ProviderAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "provider_accounts"
    __table_args__ = (UniqueConstraint("provider_kind", "provider_name", name="uq_provider_accounts_kind_name"),)

    provider_kind: Mapped[ProviderKind] = mapped_column(Enum(ProviderKind), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    health: Mapped[ProviderHealth] = mapped_column(Enum(ProviderHealth), default=ProviderHealth.OFFLINE, nullable=False)
    default_model: Mapped[str | None] = mapped_column(String(255))
    status_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_probe_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class JobRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "job_runs"

    worker_name: Mapped[str] = mapped_column(String(128), nullable=False)
    job_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Artifact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "artifacts"

    business_id: Mapped[str | None] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    artifact_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class SalesTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sales_tasks"

    business_id: Mapped[str] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    reply_event_id: Mapped[str | None] = mapped_column(ForeignKey("reply_events.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="open", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
