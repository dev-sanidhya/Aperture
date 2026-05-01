# Security Rules

## High-Risk Areas

- Secrets, provider credentials, sender accounts, webhooks, and API keys.
- Contact data, suppression entries, eligibility checks, and outreach dispatch.
- WhatsApp, email, CRM, enrichment, and public-directory integrations.

## Security Expectations

- Never log secrets, tokens, app passwords, private keys, or full sensitive payloads.
- Validate external input boundaries with explicit schemas or normalization.
- Keep least-privilege behavior for admin/protected endpoints.
- Keep WhatsApp cold outreach behind explicit eligibility and suppression rules.
- Respect opt-out, unsubscribe, suppression, and local compliance constraints.

## Verification

- Confirm no new secrets or credentials are introduced in tracked files.
- Confirm sensitive route, webhook, dispatch, and suppression changes still enforce access checks and eligibility checks.
