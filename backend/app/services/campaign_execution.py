from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.core.enums import CampaignChannel
from app.models.domain import Business, Campaign, CampaignMember, DraftMessage, EvidencePack, SendAttempt, SuppressionEntry
from app.services.dispatch import dispatch_draft
from app.services.drafts import generate_draft
from app.services.evidence import build_basic_evidence_pack


EMAIL_FOLLOWUP_DELAYS = [timedelta(days=3), timedelta(days=4)]
WHATSAPP_FOLLOWUP_DELAYS = [timedelta(days=3)]


def _max_steps(channel: CampaignChannel) -> int:
    return 3 if channel == CampaignChannel.EMAIL else 2


def _next_delay(channel: CampaignChannel, current_step: int) -> timedelta | None:
    if channel == CampaignChannel.EMAIL:
        if current_step < len(EMAIL_FOLLOWUP_DELAYS):
            return EMAIL_FOLLOWUP_DELAYS[current_step]
        return None
    if current_step < len(WHATSAPP_FOLLOWUP_DELAYS):
        return WHATSAPP_FOLLOWUP_DELAYS[current_step]
    return None


def _is_suppressed(db: Session, business_id: str) -> bool:
    return db.query(SuppressionEntry).filter(SuppressionEntry.business_id == business_id).count() > 0


def _load_or_create_evidence(db: Session, business: Business) -> EvidencePack:
    evidence = (
        db.query(EvidencePack)
        .filter(EvidencePack.business_id == business.id)
        .order_by(EvidencePack.version.desc(), EvidencePack.created_at.desc())
        .first()
    )
    if evidence is None:
        evidence = build_basic_evidence_pack(db, business)
    return evidence


def _load_existing_draft(db: Session, business_id: str, channel: CampaignChannel, sequence_step: int) -> DraftMessage | None:
    return (
        db.query(DraftMessage)
        .filter(
            DraftMessage.business_id == business_id,
            DraftMessage.channel == channel,
            DraftMessage.sequence_step == sequence_step,
        )
        .order_by(DraftMessage.created_at.desc())
        .first()
    )


def process_campaign(db: Session, campaign: Campaign) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    due_members = (
        db.query(CampaignMember)
        .filter(CampaignMember.campaign_id == campaign.id)
        .filter((CampaignMember.next_due_at.is_(None)) | (CampaignMember.next_due_at <= now))
        .filter(CampaignMember.state.in_(["queued", "ready", "sent"]))
        .order_by(CampaignMember.created_at.asc())
        .limit(campaign.daily_cap)
        .all()
    )

    processed = 0
    sent = 0
    blocked = 0

    for member in due_members:
        business = (
            db.query(Business)
            .options(joinedload(Business.contacts), joinedload(Business.segment), joinedload(Business.websites))
            .filter(Business.id == member.business_id)
            .one()
        )

        if _is_suppressed(db, business.id):
            member.state = "blocked"
            blocked += 1
            continue

        if member.last_reply_at is not None:
            member.state = "replied"
            continue

        if member.sequence_step >= _max_steps(campaign.channel):
            member.state = "completed"
            continue

        evidence = _load_or_create_evidence(db, business)
        draft = _load_existing_draft(db, business.id, campaign.channel, member.sequence_step)
        if draft is None:
            draft = generate_draft(
                db,
                business=business,
                evidence=evidence,
                channel=campaign.channel,
                sequence_step=member.sequence_step,
                template_version=campaign.template_version,
            )

        try:
            attempt = dispatch_draft(business, draft)
        except ValueError:
            member.state = "blocked"
            blocked += 1
            continue

        db.add(attempt)
        sent += 1
        processed += 1
        member.last_sent_at = now
        member.state = "sent"

        delay = _next_delay(campaign.channel, member.sequence_step)
        member.sequence_step += 1
        member.next_due_at = (now + delay) if delay is not None else None
        if member.sequence_step >= _max_steps(campaign.channel):
            member.state = "completed"

    db.flush()
    return {"processed": processed, "sent": sent, "blocked": blocked}

