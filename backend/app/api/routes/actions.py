from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_db
from app.models.domain import Business, DraftMessage, SendAttempt
from app.schemas.actions import BusinessActionRequest, DraftSendRequest, EnrichmentResponse, PipelineRunResponse
from app.schemas.api import GenericMessage
from app.services.dispatch import dispatch_draft
from app.services.discovery import enrich_business_by_id
from app.services.evidence import build_basic_evidence_pack
from app.services.scoring import compute_score


router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/score", response_model=GenericMessage)
def score_business(payload: BusinessActionRequest, db: Session = Depends(get_db)) -> GenericMessage:
    business = db.query(Business).filter(Business.id == payload.business_id).one_or_none()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found.")
    score = compute_score(db, business)
    db.commit()
    return GenericMessage(message=f"Business scored at {score.total_score}.")


@router.post("/evidence", response_model=GenericMessage)
def create_evidence(payload: BusinessActionRequest, db: Session = Depends(get_db)) -> GenericMessage:
    business = (
        db.query(Business)
        .options(joinedload(Business.segment), joinedload(Business.contacts), joinedload(Business.websites))
        .filter(Business.id == payload.business_id)
        .one_or_none()
    )
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found.")
    evidence = build_basic_evidence_pack(db, business)
    db.commit()
    return GenericMessage(message=f"Evidence pack {evidence.id} created.")


@router.post("/enrich", response_model=EnrichmentResponse)
async def enrich_business(payload: BusinessActionRequest, db: Session = Depends(get_db)) -> EnrichmentResponse:
    business = db.query(Business).filter(Business.id == payload.business_id).one_or_none()
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found.")
    result = await enrich_business_by_id(db, business.id)
    db.commit()
    return EnrichmentResponse(**result)


@router.post("/pipeline", response_model=PipelineRunResponse)
async def run_business_pipeline(payload: BusinessActionRequest, db: Session = Depends(get_db)) -> PipelineRunResponse:
    business = (
        db.query(Business)
        .options(joinedload(Business.segment), joinedload(Business.contacts), joinedload(Business.websites))
        .filter(Business.id == payload.business_id)
        .one_or_none()
    )
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found.")

    enrichment = await enrich_business_by_id(db, business.id)
    db.refresh(business)
    score = compute_score(db, business)
    db.refresh(business)
    evidence = build_basic_evidence_pack(db, business)
    db.commit()
    return PipelineRunResponse(
        **enrichment,
        score=score.total_score,
        evidence_pack_id=str(evidence.id),
    )


@router.post("/drafts/send", response_model=GenericMessage)
def send_draft(payload: DraftSendRequest, db: Session = Depends(get_db)) -> GenericMessage:
    draft = db.query(DraftMessage).filter(DraftMessage.id == payload.draft_message_id).one_or_none()
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found.")
    business = (
        db.query(Business)
        .options(joinedload(Business.contacts))
        .filter(Business.id == draft.business_id)
        .one()
    )
    draft.approved = payload.approve
    attempt = dispatch_draft(business, draft)
    db.add(attempt)
    db.commit()
    return GenericMessage(message=f"Draft dispatched with status {attempt.status}.")
