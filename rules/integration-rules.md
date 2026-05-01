# Integration Rules

## External Providers

- Use explicit timeouts, retries only when safe, and clear failure modes for network calls.
- Keep provider-specific payloads behind integration modules where possible.
- Do not hardcode credentials, account IDs, phone numbers, or sender identities.

## Discovery and Outreach

- Prefer public business websites, search results, directories, and explicit provider APIs over brittle scraping.
- Do not aggressively scrape LinkedIn or private/member-only surfaces.
- Treat search scraping as opportunistic; validate output quality before scaling.

## Messaging

- Do not use one-off Gmail scripts as production sending infrastructure.
- Prefer domain-authenticated sequencing via SES, Instantly, Smartlead, or another explicit provider integration.
- Preserve unsubscribe/suppression handling and sender reputation safeguards.
