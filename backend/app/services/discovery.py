from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.core.enums import BusinessState, ChannelType, SendEligibility, SourceType, VerificationStatus
from app.integrations.discovery.directories import DirectoryClient
from app.integrations.discovery.search import SearchClient, SearchResult
from app.integrations.discovery.websites import WebsiteClient
from app.models.domain import Business, BusinessLocation, ContactPoint, LeadSegment, SourceRecord, Website
from app.services.normalization import (
    is_directory_domain,
    is_social_domain,
    normalize_domain,
    normalize_name,
    normalize_phone,
)
from app.services.routing import build_segment


def _coerce_state(place: dict) -> BusinessState:
    if place.get("websiteUri"):
        return BusinessState.HAS_WEBSITE_WEAK
    return BusinessState.NO_WEBSITE


def _source_type_from_url(url: str) -> SourceType:
    if is_directory_domain(url):
        domain = normalize_domain(url)
        if domain == "justdial.com":
            return SourceType.JUSTDIAL
        if domain == "indiamart.com":
            return SourceType.INDIAMART
        return SourceType.SEARCH
    if is_social_domain(url):
        return SourceType.SOCIAL
    return SourceType.WEBSITE


def _upsert_contact(
    db: Session,
    *,
    business: Business,
    channel: ChannelType,
    value: str,
    source_url: str | None,
    whatsapp_likely: bool = False,
    confidence: float = 0.8,
) -> ContactPoint:
    existing = (
        db.query(ContactPoint)
        .filter(ContactPoint.business_id == business.id, ContactPoint.channel == channel, ContactPoint.value == value)
        .one_or_none()
    )
    if existing is not None:
        existing.confidence = max(existing.confidence, confidence)
        existing.source_url = source_url or existing.source_url
        existing.whatsapp_likely = existing.whatsapp_likely or whatsapp_likely
        existing.verification_status = VerificationStatus.OBSERVED_PUBLIC
        if channel in {ChannelType.EMAIL, ChannelType.WHATSAPP}:
            existing.send_eligibility = SendEligibility.ELIGIBLE
        return existing

    contact = ContactPoint(
        business_id=business.id,
        channel=channel,
        value=value,
        public_business_contact=True,
        verification_status=VerificationStatus.OBSERVED_PUBLIC,
        confidence=confidence,
        source_url=source_url,
        whatsapp_likely=whatsapp_likely,
        send_eligibility=SendEligibility.ELIGIBLE if channel in {ChannelType.EMAIL, ChannelType.WHATSAPP} else SendEligibility.HOLD,
    )
    db.add(contact)
    db.flush()
    return contact


def _sync_segment(db: Session, business: Business) -> LeadSegment:
    contacts = db.query(ContactPoint).filter(ContactPoint.business_id == business.id).all()
    segment = db.query(LeadSegment).filter(LeadSegment.business_id == business.id).one_or_none()
    computed = build_segment(business, contacts)
    if segment is None:
        db.add(computed)
        db.flush()
        return computed

    segment.state = computed.state
    segment.service_lane = computed.service_lane
    segment.routing_channel = computed.routing_channel
    segment.routing_tier = computed.routing_tier
    segment.rationale = computed.rationale
    db.flush()
    return segment


def _upsert_source(
    db: Session,
    *,
    business: Business,
    source_type: SourceType,
    source_url: str | None,
    source_id: str | None,
    raw_payload: dict,
    parser_version: str,
) -> SourceRecord:
    existing = (
        db.query(SourceRecord)
        .filter(
            SourceRecord.business_id == business.id,
            SourceRecord.source_type == source_type,
            SourceRecord.source_url == source_url,
        )
        .one_or_none()
    )
    if existing is not None:
        existing.raw_payload = raw_payload
        existing.parser_version = parser_version
        return existing

    record = SourceRecord(
        business_id=business.id,
        source_type=source_type,
        source_id=source_id,
        source_url=source_url,
        raw_payload=raw_payload,
        parser_version=parser_version,
    )
    db.add(record)
    db.flush()
    return record


def _upsert_website(db: Session, *, business: Business, url: str, audit_summary: str | None = None) -> Website:
    normalized = normalize_domain(url)
    existing = db.query(Website).filter(Website.business_id == business.id, Website.normalized_domain == normalized).one_or_none()
    if existing is not None:
        existing.url = url
        if audit_summary:
            existing.audit_summary = audit_summary
        return existing

    website = Website(
        business_id=business.id,
        url=url,
        normalized_domain=normalized,
        crawl_state="fetched",
        is_weak=True,
        audit_summary=audit_summary,
    )
    db.add(website)
    db.flush()
    return website


def ingest_places_payload(db: Session, places: Iterable[dict]) -> tuple[int, int]:
    imported = 0
    updated = 0

    for place in places:
        place_id = place.get("id")
        display = place.get("displayName") or {}
        name = display.get("text") or "Unknown business"
        formatted_address = place.get("formattedAddress")
        primary_type = place.get("primaryType")
        website_url = place.get("websiteUri")
        national_phone = place.get("nationalPhoneNumber")
        international_phone = place.get("internationalPhoneNumber")
        location = place.get("location") or {}

        business = db.query(Business).filter(Business.google_place_id == place_id).one_or_none()
        if business is None:
            business = Business(
                name=name,
                normalized_name=normalize_name(name),
                google_place_id=place_id,
                normalized_domain=normalize_domain(website_url) if website_url else None,
                normalized_phone=normalize_phone(international_phone or national_phone) if (international_phone or national_phone) else None,
                state=_coerce_state(place),
                city=formatted_address,
                category=primary_type,
                priority_score=45.0,
            )
            db.add(business)
            db.flush()
            imported += 1
        else:
            business.name = name
            business.normalized_name = normalize_name(name)
            business.state = _coerce_state(place)
            business.category = primary_type
            business.city = formatted_address
            if website_url:
                business.normalized_domain = normalize_domain(website_url)
            if international_phone or national_phone:
                business.normalized_phone = normalize_phone(international_phone or national_phone)
            updated += 1

        _upsert_source(
            db,
            business=business,
            source_type=SourceType.GOOGLE_PLACES,
            source_id=place_id,
            source_url=None,
            raw_payload=place,
            parser_version="places-v1",
        )

        if formatted_address:
            location_row = (
                db.query(BusinessLocation).filter(BusinessLocation.business_id == business.id, BusinessLocation.address == formatted_address).one_or_none()
            )
            if location_row is None:
                db.add(
                    BusinessLocation(
                        business_id=business.id,
                        address=formatted_address,
                        city=formatted_address,
                        latitude=location.get("latitude"),
                        longitude=location.get("longitude"),
                    )
                )

        if website_url:
            _upsert_website(db, business=business, url=website_url)

        phone_value = normalize_phone(international_phone or national_phone) if (international_phone or national_phone) else None
        if phone_value:
            _upsert_contact(db, business=business, channel=ChannelType.PHONE, value=phone_value, source_url=None)
            _upsert_contact(db, business=business, channel=ChannelType.WHATSAPP, value=phone_value, source_url=None, whatsapp_likely=True)

        _sync_segment(db, business)

    db.flush()
    return imported, updated


def _search_queries(business: Business) -> list[str]:
    parts = [business.name]
    if business.city:
        parts.append(business.city)
    if business.category:
        parts.append(business.category)
    base = " ".join(part for part in parts if part)
    return [
        f'"{business.name}" "{business.city or ""}"',
        f"{base} contact",
        f"{base} website",
        f"{base} Justdial",
        f"{base} IndiaMART",
    ]


async def enrich_business_from_secondary_sources(
    db: Session,
    *,
    business: Business,
    search_client: SearchClient | None = None,
    website_client: WebsiteClient | None = None,
    directory_client: DirectoryClient | None = None,
) -> dict[str, int]:
    search_client = search_client or SearchClient()
    website_client = website_client or WebsiteClient()
    directory_client = directory_client or DirectoryClient()

    queries = _search_queries(business)
    seen_urls: set[str] = set()
    source_count = 0
    contact_count = 0
    website_count = 0

    for query in queries:
        results = await search_client.search(query, max_results=5)
        for result in results:
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)

            source_type = _source_type_from_url(result.url)
            _upsert_source(
                db,
                business=business,
                source_type=source_type,
                source_id=None,
                source_url=result.url,
                raw_payload={"title": result.title, "snippet": result.snippet, "query": query},
                parser_version="search-v1",
            )
            source_count += 1

            if source_type == SourceType.WEBSITE:
                extraction = await website_client.extract(result.url)
                if extraction is None:
                    continue
                _upsert_website(db, business=business, url=extraction.final_url, audit_summary=extraction.audit_summary)
                website_count += 1
                business.normalized_domain = business.normalized_domain or normalize_domain(extraction.final_url)
                if business.state == BusinessState.NO_WEBSITE:
                    business.state = BusinessState.HAS_WEBSITE_WEAK

                for email in extraction.emails:
                    _upsert_contact(db, business=business, channel=ChannelType.EMAIL, value=email, source_url=extraction.final_url, confidence=0.9)
                    contact_count += 1
                for phone in extraction.phones:
                    _upsert_contact(db, business=business, channel=ChannelType.PHONE, value=phone, source_url=extraction.final_url, confidence=0.85)
                    contact_count += 1
                for phone in extraction.whatsapp_numbers:
                    _upsert_contact(
                        db,
                        business=business,
                        channel=ChannelType.WHATSAPP,
                        value=phone,
                        source_url=extraction.final_url,
                        whatsapp_likely=True,
                        confidence=0.95,
                    )
                    contact_count += 1

                for social_link in extraction.social_links:
                    social_type = _source_type_from_url(social_link)
                    _upsert_source(
                        db,
                        business=business,
                        source_type=social_type,
                        source_id=None,
                        source_url=social_link,
                        raw_payload={"discovered_from": extraction.final_url},
                        parser_version="website-social-v1",
                    )
                    source_count += 1
            elif source_type in {SourceType.JUSTDIAL, SourceType.INDIAMART, SourceType.SEARCH} and is_directory_domain(result.url):
                extraction = await directory_client.extract(result.url)
                if extraction is None:
                    continue

                _upsert_source(
                    db,
                    business=business,
                    source_type=source_type,
                    source_id=None,
                    source_url=extraction.final_url,
                    raw_payload={
                        "title": result.title,
                        "snippet": result.snippet,
                        "query": query,
                        "notes": extraction.notes,
                    },
                    parser_version="directory-v1",
                )
                for email in extraction.emails:
                    _upsert_contact(db, business=business, channel=ChannelType.EMAIL, value=email, source_url=extraction.final_url, confidence=0.75)
                    contact_count += 1
                for phone in extraction.phones:
                    _upsert_contact(db, business=business, channel=ChannelType.PHONE, value=phone, source_url=extraction.final_url, confidence=0.7)
                    contact_count += 1
                for phone in extraction.whatsapp_numbers:
                    _upsert_contact(
                        db,
                        business=business,
                        channel=ChannelType.WHATSAPP,
                        value=phone,
                        source_url=extraction.final_url,
                        whatsapp_likely=True,
                        confidence=0.8,
                    )
                    contact_count += 1
                for website_url in extraction.website_urls:
                    _upsert_website(db, business=business, url=website_url, audit_summary=extraction.notes)
                    website_count += 1
                    business.normalized_domain = business.normalized_domain or normalize_domain(website_url)
                    if business.state == BusinessState.NO_WEBSITE:
                        business.state = BusinessState.HAS_WEBSITE_WEAK
                for social_link in extraction.social_links:
                    _upsert_source(
                        db,
                        business=business,
                        source_type=_source_type_from_url(social_link),
                        source_id=None,
                        source_url=social_link,
                        raw_payload={"discovered_from": extraction.final_url},
                        parser_version="directory-social-v1",
                    )
                    source_count += 1

    _sync_segment(db, business)
    db.flush()
    return {"sources_added": source_count, "contacts_added": contact_count, "websites_added": website_count}


async def enrich_business_by_id(db: Session, business_id: str) -> dict[str, int]:
    business = db.query(Business).filter(Business.id == business_id).one()
    return await enrich_business_from_secondary_sources(db, business=business)


def search_result_to_source(result: SearchResult, query: str) -> dict:
    return {"title": result.title, "snippet": result.snippet, "query": query, "url": result.url}
