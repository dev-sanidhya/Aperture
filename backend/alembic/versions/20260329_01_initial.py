"""initial schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260329_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    channeltype = postgresql.ENUM("EMAIL", "PHONE", "WHATSAPP", "CONTACT_FORM", "SOCIAL_DM", "CALL_REVIEW", name="channeltype", create_type=False)
    businessstate = postgresql.ENUM("NO_WEBSITE", "HAS_WEBSITE_WEAK", "HAS_WEBSITE_OK", name="businessstate", create_type=False)
    servicelane = postgresql.ENUM(
        "new_web_presence",
        "website_rebuild_cro",
        "local_seo_maps",
        "ai_automation",
        "lead_capture_booking",
        name="servicelane",
        create_type=False,
    )
    verificationstatus = postgresql.ENUM("unverified", "observed_public", "verified_live", "invalid", name="verificationstatus", create_type=False)
    sendeligibility = postgresql.ENUM("eligible", "hold", "blocked", name="sendeligibility", create_type=False)
    sourcetype = postgresql.ENUM("google_places", "website", "justdial", "indiamart", "social", "search", name="sourcetype", create_type=False)
    campaignchannel = postgresql.ENUM("email", "whatsapp", name="campaignchannel", create_type=False)
    campaignstatus = postgresql.ENUM("draft", "ready", "running", "paused", "completed", name="campaignstatus", create_type=False)
    providerkind = postgresql.ENUM("openclaw", "ses", "twilio", name="providerkind", create_type=False)
    providerhealth = postgresql.ENUM("healthy", "degraded", "offline", name="providerhealth", create_type=False)
    airunjobtype = postgresql.ENUM(
        "lead_enrichment",
        "contact_discovery",
        "site_audit",
        "draft_email",
        "draft_whatsapp",
        "reply_classifier",
        "opportunity_scoring",
        name="airunjobtype",
        create_type=False,
    )
    airunstatus = postgresql.ENUM("pending", "succeeded", "failed", name="airunstatus", create_type=False)
    messagedirection = postgresql.ENUM("OUTBOUND", "INBOUND", name="messagedirection", create_type=False)
    replyintent = postgresql.ENUM(
        "interested",
        "not_now",
        "not_relevant",
        "wrong_contact",
        "unsubscribe",
        "hostile",
        "spam_signal",
        "unknown",
        name="replyintent",
        create_type=False,
    )
    suppressionreason = postgresql.ENUM("unsubscribe", "complaint", "global_block", "channel_block", "cooldown", name="suppressionreason", create_type=False)

    bind = op.get_bind()
    enums = [
        channeltype,
        businessstate,
        servicelane,
        verificationstatus,
        sendeligibility,
        sourcetype,
        campaignchannel,
        campaignstatus,
        providerkind,
        providerhealth,
        airunjobtype,
        airunstatus,
        messagedirection,
        replyintent,
        suppressionreason,
    ]
    for enum in enums:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "businesses",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("google_place_id", sa.String(length=255), nullable=True),
        sa.Column("normalized_domain", sa.String(length=255), nullable=True),
        sa.Column("normalized_phone", sa.String(length=64), nullable=True),
        sa.Column("state", businessstate, nullable=False),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("subcategory", sa.String(length=128), nullable=True),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_businesses"),
        sa.UniqueConstraint("google_place_id", name="uq_businesses_google_place_id"),
    )
    op.create_index("ix_businesses_normalized_name", "businesses", ["normalized_name"])
    op.create_index("ix_businesses_normalized_domain", "businesses", ["normalized_domain"])
    op.create_index("ix_businesses_normalized_phone", "businesses", ["normalized_phone"])

    op.create_table(
        "business_locations",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("address", sa.String(length=512), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("area", sa.String(length=128), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_business_locations_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_business_locations"),
    )
    op.create_index("ix_business_locations_city", "business_locations", ["city"])

    op.create_table(
        "source_records",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", sourcetype, nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_source_records_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_source_records"),
    )
    op.create_index("ix_source_records_source_id", "source_records", ["source_id"])
    op.create_index("ix_source_records_source_type", "source_records", ["source_type"])

    op.create_table(
        "websites",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("normalized_domain", sa.String(length=255), nullable=False),
        sa.Column("crawl_state", sa.String(length=64), nullable=False),
        sa.Column("is_weak", sa.Boolean(), nullable=False),
        sa.Column("audit_summary", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_websites_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_websites"),
    )
    op.create_index("ix_websites_normalized_domain", "websites", ["normalized_domain"])

    op.create_table(
        "contact_points",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", channeltype, nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("public_business_contact", sa.Boolean(), nullable=False),
        sa.Column("verification_status", verificationstatus, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("whatsapp_likely", sa.Boolean(), nullable=False),
        sa.Column("send_eligibility", sendeligibility, nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_contact_points_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_contact_points"),
        sa.UniqueConstraint("business_id", "channel", "value", name="uq_contact_points_business_channel_value"),
    )
    op.create_index("ix_contact_points_channel", "contact_points", ["channel"])

    op.create_table(
        "lead_segments",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state", businessstate, nullable=False),
        sa.Column("service_lane", servicelane, nullable=False),
        sa.Column("routing_channel", channeltype, nullable=False),
        sa.Column("routing_tier", sa.String(length=64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_lead_segments_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_lead_segments"),
        sa.UniqueConstraint("business_id", name="uq_lead_segments_business_id"),
    )

    for name in ("evidence_packs", "opportunity_scores", "campaigns", "campaign_members", "message_templates", "ai_runs", "draft_messages", "send_attempts", "reply_events", "suppression_entries", "provider_accounts", "job_runs", "artifacts"):
        pass

    op.create_table(
        "evidence_packs",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observed_issue", sa.Text(), nullable=False),
        sa.Column("consequence", sa.Text(), nullable=False),
        sa.Column("offer_match", servicelane, nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_evidence_packs_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_evidence_packs"),
    )

    op.create_table(
        "opportunity_scores",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_opportunity_scores_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_opportunity_scores"),
    )

    op.create_table(
        "campaigns",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("channel", campaignchannel, nullable=False),
        sa.Column("status", campaignstatus, nullable=False),
        sa.Column("template_version", sa.String(length=64), nullable=False),
        sa.Column("daily_cap", sa.Integer(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_campaigns"),
    )

    op.create_table(
        "campaign_members",
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_step", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_campaign_members_business_id_businesses", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], name="fk_campaign_members_campaign_id_campaigns", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_campaign_members"),
        sa.UniqueConstraint("campaign_id", "business_id", name="uq_campaign_members_campaign_business"),
    )

    op.create_table(
        "message_templates",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("channel", campaignchannel, nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_message_templates"),
    )

    op.create_table(
        "ai_runs",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider_name", sa.String(length=128), nullable=False),
        sa.Column("model_alias", sa.String(length=128), nullable=False),
        sa.Column("job_type", airunjobtype, nullable=False),
        sa.Column("status", airunstatus, nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_ai_runs_business_id_businesses", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_runs"),
    )

    op.create_table(
        "draft_messages",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_pack_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ai_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", campaignchannel, nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("template_version", sa.String(length=64), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["ai_run_id"], ["ai_runs.id"], name="fk_draft_messages_ai_run_id_ai_runs", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_draft_messages_business_id_businesses", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_pack_id"], ["evidence_packs.id"], name="fk_draft_messages_evidence_pack_id_evidence_packs", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_draft_messages"),
    )

    op.create_table(
        "send_attempts",
        sa.Column("draft_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction", messagedirection, nullable=False),
        sa.Column("provider_kind", providerkind, nullable=False),
        sa.Column("channel", campaignchannel, nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_send_attempts_business_id_businesses", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["draft_message_id"], ["draft_messages.id"], name="fk_send_attempts_draft_message_id_draft_messages", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_send_attempts"),
        sa.UniqueConstraint("idempotency_key", name="uq_send_attempts_idempotency_key"),
    )

    op.create_table(
        "reply_events",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("send_attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider_kind", providerkind, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("intent", replyintent, nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_reply_events_business_id_businesses", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["send_attempt_id"], ["send_attempts.id"], name="fk_reply_events_send_attempt_id_send_attempts", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_reply_events"),
    )

    op.create_table(
        "suppression_entries",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", channeltype, nullable=True),
        sa.Column("reason", suppressionreason, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_suppression_entries_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_suppression_entries"),
    )

    op.create_table(
        "provider_accounts",
        sa.Column("provider_kind", providerkind, nullable=False),
        sa.Column("provider_name", sa.String(length=128), nullable=False),
        sa.Column("health", providerhealth, nullable=False),
        sa.Column("default_model", sa.String(length=255), nullable=True),
        sa.Column("status_payload", sa.JSON(), nullable=False),
        sa.Column("last_probe_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_provider_accounts"),
        sa.UniqueConstraint("provider_kind", "provider_name", name="uq_provider_accounts_kind_name"),
    )

    op.create_table(
        "job_runs",
        sa.Column("worker_name", sa.String(length=128), nullable=False),
        sa.Column("job_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_job_runs"),
    )

    op.create_table(
        "artifacts",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("artifact_type", sa.String(length=128), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], name="fk_artifacts_business_id_businesses", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_artifacts"),
    )


def downgrade() -> None:
    for table in [
        "artifacts",
        "job_runs",
        "provider_accounts",
        "suppression_entries",
        "reply_events",
        "send_attempts",
        "draft_messages",
        "ai_runs",
        "message_templates",
        "campaign_members",
        "campaigns",
        "opportunity_scores",
        "evidence_packs",
        "lead_segments",
        "contact_points",
        "websites",
        "source_records",
        "business_locations",
        "businesses",
    ]:
        op.drop_table(table)

    bind = op.get_bind()
    for enum_name in [
        "suppressionreason",
        "replyintent",
        "messagedirection",
        "airunstatus",
        "airunjobtype",
        "providerhealth",
        "providerkind",
        "campaignstatus",
        "campaignchannel",
        "sourcetype",
        "sendeligibility",
        "verificationstatus",
        "servicelane",
        "businessstate",
        "channeltype",
    ]:
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
