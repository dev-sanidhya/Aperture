# contact-discovery

Extract public business contacts for an approved B2B agency account using only the provided evidence.

Return strict JSON with exactly:

- `contacts`
- `best_contact`
- `missing_info`
- `manual_verification_needed`
- `confidence_notes`

Each contact must include:

- `name`
- `title`
- `role_fit`
- `linkedin_url`
- `email`
- `phone`
- `source_url`
- `public_business_contact`
- `confidence`
- `notes`

Rules:

- Do not invent contacts, email addresses, LinkedIn profiles, titles, or verification status.
- Prefer founder, CEO, managing director, COO, operations, RevOps, or client-services leadership contacts.
- Public generic emails are allowed, but label them as business contacts rather than decision makers.
- Mark guessed or incomplete data in `missing_info`; never present it as verified.
- Output JSON only.

