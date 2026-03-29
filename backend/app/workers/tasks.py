from __future__ import annotations

import dramatiq
from sqlalchemy.orm import joinedload

from app.core.db import session_scope
from app.core.enums import AIRunJobType
from app.models.domain import Business, Campaign, DraftMessage, ReplyEvent
from app.services.campaigns import materialize_campaign_members
from app.services.discovery import enrich_business_by_id
from app.services.dispatch import dispatch_draft
from app.services.evidence import build_basic_evidence_pack
from app.services.openclaw_jobs import run_openclaw_job
from app.services.provider_health import sync_openclaw_health
from app.services.replies import apply_reply_outcome
from app.services.scoring import compute_score
from app.workers.broker import broker


@dramatiq.actor(broker=broker)
def refresh_openclaw_status() -> None:
    with session_scope() as db:
        sync_openclaw_health(db)


@dramatiq.actor(broker=broker)
def run_lead_enrichment(business_id: str) -> None:
    with session_scope() as db:
        business = (
            db.query(Business)
            .options(joinedload(Business.sources), joinedload(Business.contacts), joinedload(Business.websites))
            .filter(Business.id == business_id)
            .one()
        )
        run_openclaw_job(
            db,
            business=business,
            job_type=AIRunJobType.LEAD_ENRICHMENT,
            model_alias="cheap_fast",
            message_payload={
                "business": business.name,
                "city": business.city,
                "category": business.category,
                "sources": [source.raw_payload for source in business.sources],
            },
        )


@dramatiq.actor(broker=broker)
def enrich_secondary_sources(business_id: str) -> None:
    with session_scope() as db:
        import asyncio

        asyncio.run(enrich_business_by_id(db, business_id))


@dramatiq.actor(broker=broker)
def compute_business_score(business_id: str) -> None:
    with session_scope() as db:
        business = db.query(Business).filter(Business.id == business_id).one()
        compute_score(db, business)


@dramatiq.actor(broker=broker)
def create_evidence_pack(business_id: str) -> None:
    with session_scope() as db:
        business = (
            db.query(Business)
            .options(joinedload(Business.segment), joinedload(Business.contacts), joinedload(Business.websites))
            .filter(Business.id == business_id)
            .one()
        )
        build_basic_evidence_pack(db, business)


@dramatiq.actor(broker=broker)
def run_full_lead_pipeline(business_id: str) -> None:
    with session_scope() as db:
        import asyncio

        business = (
            db.query(Business)
            .options(joinedload(Business.segment), joinedload(Business.contacts), joinedload(Business.websites))
            .filter(Business.id == business_id)
            .one()
        )
        asyncio.run(enrich_business_by_id(db, business_id))
        compute_score(db, business)
        build_basic_evidence_pack(db, business)


@dramatiq.actor(broker=broker)
def launch_campaign_members(campaign_id: str) -> None:
    with session_scope() as db:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).one()
        materialize_campaign_members(db, campaign)


@dramatiq.actor(broker=broker)
def send_draft_message(draft_message_id: str) -> None:
    with session_scope() as db:
        draft = db.query(DraftMessage).filter(DraftMessage.id == draft_message_id).one()
        business = db.query(Business).options(joinedload(Business.contacts)).filter(Business.id == draft.business_id).one()
        attempt = dispatch_draft(business, draft)
        db.add(attempt)


@dramatiq.actor(broker=broker)
def apply_reply(reply_event_id: str) -> None:
    with session_scope() as db:
        reply = db.query(ReplyEvent).filter(ReplyEvent.id == reply_event_id).one()
        business = db.query(Business).filter(Business.id == reply.business_id).one()
        apply_reply_outcome(db, business=business, reply=reply)
