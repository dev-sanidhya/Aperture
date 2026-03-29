from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import SourceType
from app.models.domain import Business, ContactPoint, EvidencePack, SourceRecord, Website


def build_basic_evidence_pack(db: Session, business: Business) -> EvidencePack:
    contacts = db.query(ContactPoint).filter(ContactPoint.business_id == business.id).all()
    websites = db.query(Website).filter(Website.business_id == business.id).all()
    sources = db.query(SourceRecord).filter(SourceRecord.business_id == business.id).all()
    has_directory_presence = any(source.source_type in {SourceType.JUSTDIAL, SourceType.INDIAMART} for source in sources)

    if business.state.value == "NO_WEBSITE":
        observed_issue = "The business does not appear to have a direct website presence."
        if has_directory_presence:
            consequence = "Customers depend on directory listings instead of reaching the business through a direct branded channel."
        else:
            consequence = "Customers depend on third-party listings instead of contacting the business directly."
    elif websites:
        observed_issue = websites[0].audit_summary or "The website likely creates friction for enquiries or trust."
        consequence = "Visitors may drop without converting into direct enquiries."
    else:
        observed_issue = "The digital presence is incomplete or unclear."
        consequence = "Potential customers may not find a reliable direct contact path."

    offer_match = business.segment.service_lane if business.segment else None
    if offer_match is None:
        raise ValueError("Lead segment must exist before generating evidence.")

    evidence = EvidencePack(
        business_id=business.id,
        observed_issue=observed_issue,
        consequence=consequence,
        offer_match=offer_match,
        evidence_json={
            "website_count": len(websites),
            "contact_count": len(contacts),
            "source_count": len(sources),
            "directory_presence": has_directory_presence,
            "category": business.category,
            "city": business.city,
        },
        version=1,
    )
    db.add(evidence)
    db.flush()
    return evidence
