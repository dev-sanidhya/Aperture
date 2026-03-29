from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.enums import ProviderKind, ReplyIntent
from app.models.domain import ReplyEvent, SendAttempt
from app.schemas.api import GenericMessage


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _resolve_business_id(db: Session, payload: dict, provider_kind: ProviderKind) -> str | None:
    if payload.get("business_id"):
        return payload["business_id"]

    provider_message_id = payload.get("provider_message_id") or payload.get("MessageSid") or payload.get("messageId")
    if provider_message_id:
        attempt = (
            db.query(SendAttempt)
            .filter(SendAttempt.provider_kind == provider_kind, SendAttempt.provider_message_id == provider_message_id)
            .one_or_none()
        )
        if attempt is not None:
            return str(attempt.business_id)
    return None


@router.post("/email", response_model=GenericMessage)
async def email_webhook(request: Request, db: Session = Depends(get_db)) -> GenericMessage:
    payload = await request.json()
    business_id = _resolve_business_id(db, payload, ProviderKind.SES)
    if business_id:
        db.add(
            ReplyEvent(
                business_id=business_id,
                provider_kind=ProviderKind.SES,
                payload=payload,
                normalized_text=payload.get("text") or payload.get("body"),
                intent=ReplyIntent.UNKNOWN,
            )
        )
        db.commit()
    return GenericMessage(message="Email webhook received.")


@router.post("/whatsapp", response_model=GenericMessage)
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)) -> GenericMessage:
    payload = await request.json()
    business_id = _resolve_business_id(db, payload, ProviderKind.TWILIO)
    if business_id:
        db.add(
            ReplyEvent(
                business_id=business_id,
                provider_kind=ProviderKind.TWILIO,
                payload=payload,
                normalized_text=payload.get("Body") or payload.get("body"),
                intent=ReplyIntent.UNKNOWN,
            )
        )
        db.commit()
    return GenericMessage(message="WhatsApp webhook received.")
