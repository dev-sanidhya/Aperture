from __future__ import annotations

from app.core.enums import CampaignChannel, MessageDirection, ProviderKind
from app.integrations.messaging.ses import SESClient, SESDispatchRequest
from app.integrations.messaging.twilio_whatsapp import TwilioWhatsAppClient, TwilioWhatsAppDispatchRequest
from app.models.domain import Business, DraftMessage, SendAttempt


def idempotency_key(business: Business, draft: DraftMessage) -> str:
    return f"{business.id}:{draft.id}:{draft.channel.value}"


def dispatch_draft(business: Business, draft: DraftMessage) -> SendAttempt:
    key = idempotency_key(business, draft)
    if draft.channel == CampaignChannel.EMAIL:
        email_contact = next((c for c in business.contacts if c.channel.value == "email"), None)
        if email_contact is None:
            raise ValueError("No eligible email contact found for business.")
        to_email = email_contact.value
        result = SESClient().send_email(SESDispatchRequest(to_email=to_email, subject=draft.subject or "", body=draft.body))
        return SendAttempt(
            draft_message_id=draft.id,
            business_id=business.id,
            direction=MessageDirection.OUTBOUND,
            provider_kind=ProviderKind.SES,
            channel=draft.channel,
            idempotency_key=key,
            provider_message_id=result["provider_message_id"],
            status=result["status"],
        )

    phone_contact = next((c for c in business.contacts if c.channel.value == "whatsapp"), None)
    if phone_contact is None:
        raise ValueError("No eligible WhatsApp contact found for business.")
    to_number = phone_contact.value
    result = TwilioWhatsAppClient().send_whatsapp(TwilioWhatsAppDispatchRequest(to_number=to_number, body=draft.body))
    return SendAttempt(
        draft_message_id=draft.id,
        business_id=business.id,
        direction=MessageDirection.OUTBOUND,
        provider_kind=ProviderKind.TWILIO,
        channel=draft.channel,
        idempotency_key=key,
        provider_message_id=result["provider_message_id"],
        status=result["status"],
    )

