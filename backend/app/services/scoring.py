from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import BusinessState, ChannelType, SourceType
from app.models.domain import Business, ContactPoint, OpportunityScore, SourceRecord, Website


def compute_score(db: Session, business: Business) -> OpportunityScore:
    contacts = db.query(ContactPoint).filter(ContactPoint.business_id == business.id).all()
    sources = db.query(SourceRecord).filter(SourceRecord.business_id == business.id).all()
    websites = db.query(Website).filter(Website.business_id == business.id).all()
    reasons: dict[str, float] = {}
    total = 0.0

    if business.state == BusinessState.NO_WEBSITE:
        reasons["no_website"] = 30
        total += 30
    elif business.state == BusinessState.HAS_WEBSITE_WEAK:
        reasons["weak_website"] = 22
        total += 22

    if any(contact.channel == ChannelType.EMAIL for contact in contacts):
        reasons["public_email"] = 10
        total += 10

    if any(contact.channel == ChannelType.WHATSAPP and contact.whatsapp_likely for contact in contacts):
        reasons["whatsapp_ready"] = 12
        total += 12

    if any(source.source_type in {SourceType.JUSTDIAL, SourceType.INDIAMART} for source in sources):
        reasons["directory_presence"] = 8
        total += 8

    if business.category:
        reasons["category_present"] = 8
        total += 8

    if websites and any(website.audit_summary for website in websites):
        reasons["site_audit_available"] = 10
        total += 10

    score = db.query(OpportunityScore).filter(OpportunityScore.business_id == business.id).one_or_none()
    if score is None:
        score = OpportunityScore(business_id=business.id, total_score=total, reasons=reasons)
        db.add(score)
    else:
        score.total_score = total
        score.reasons = reasons

    business.priority_score = total
    db.flush()
    return score
