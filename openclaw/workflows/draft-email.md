# draft-email

Write outreach drafts for Aperture using only the provided account, contact, and evidence payload.

Return strict JSON with exactly:

- `workflow_gap`
- `evidence`
- `assumptions`
- `best_contact_name`
- `best_contact_title`
- `best_contact_linkedin`
- `best_contact_email`
- `linkedin_connect`
- `linkedin_followup`
- `cold_email_subject`
- `cold_email_body`
- `followup_1`
- `loom_teardown_plan`
- `call_questions`
- `manual_checks`
- `do_not_claim`
- `pitch_status`

Rules:

- Do not invent metrics, current tools, customer names, contacts, or email addresses.
- Keep emails short, plain-text, and founder-led.
- The CTA should ask whether they are open to 2-3 specific automation ideas or a short teardown.
- Use `manual_checks` to list anything that must be verified before sending.
- Use `do_not_claim` for claims the sender must avoid.
- Output JSON only.

