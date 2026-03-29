from __future__ import annotations

from app.core.enums import AIRunJobType, CampaignChannel
from app.models.domain import Business, DraftMessage, EvidencePack
from app.services.openclaw_jobs import run_openclaw_job


def draft_subject(business: Business, step: int) -> str:
    if step == 0:
        return f"Quick idea for {business.name}"
    if step == 1:
        return f"Following up on {business.name}"
    return f"Last note for {business.name}"


def generate_draft(
    db,
    *,
    business: Business,
    evidence: EvidencePack,
    channel: CampaignChannel,
    sequence_step: int,
    template_version: str,
) -> DraftMessage:
    job_type = AIRunJobType.DRAFT_EMAIL if channel == CampaignChannel.EMAIL else AIRunJobType.DRAFT_WHATSAPP
    model_alias = "quality_draft" if channel == CampaignChannel.EMAIL else "cheap_fast"
    run = run_openclaw_job(
        db,
        business=business,
        job_type=job_type,
        model_alias=model_alias,
        message_payload={
            "business_name": business.name,
            "city": business.city,
            "issue": evidence.observed_issue,
            "consequence": evidence.consequence,
            "service_lane": evidence.offer_match.value,
            "sequence_step": sequence_step,
            "followup_context": "initial outreach" if sequence_step == 0 else f"follow-up step {sequence_step}",
        },
    )
    body = run.output_json.get("reply") or run.output_json.get("text") or str(run.output_json)
    draft = DraftMessage(
        business_id=business.id,
        evidence_pack_id=evidence.id,
        ai_run_id=run.id,
        channel=channel,
        sequence_step=sequence_step,
        subject=draft_subject(business, sequence_step) if channel == CampaignChannel.EMAIL else None,
        body=body,
        template_version=template_version,
        approved=True,
    )
    db.add(draft)
    db.flush()
    return draft

