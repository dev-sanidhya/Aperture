# Provider Setup

## What Aperture needs

These values go into `.env` at the project root.

## Database and Redis

### `APERTURE_DATABASE_URL`

Example:

```env
APERTURE_DATABASE_URL=postgresql+psycopg://aperture:CHANGE_ME@localhost:5432/aperture
```

### `APERTURE_REDIS_URL`

Example:

```env
APERTURE_REDIS_URL=redis://localhost:6379/0
```

## Google Places

### `APERTURE_GOOGLE_PLACES_API_KEY`

How to get it:
1. Open Google Cloud Console.
2. Create a project for Aperture.
3. Enable `Places API (New)`.
4. Enable billing.
5. Go to `APIs & Services -> Credentials`.
6. Create an API key.
7. Restrict the key to the Places API and to your server IP if possible.

## Amazon SES

### What you need

- `APERTURE_SES_REGION`
- `APERTURE_AWS_ACCESS_KEY_ID`
- `APERTURE_AWS_SECRET_ACCESS_KEY`
- `APERTURE_AWS_SESSION_TOKEN`  
  usually blank unless you use temporary credentials
- `APERTURE_OUTREACH_DOMAIN`

### Setup flow

1. Create an AWS account if you do not already have one.
2. Open `Amazon SES`.
3. Verify your sending domain or subdomain, for example `outreach.yourdomain.com`.
4. Add the DNS records SES gives you for domain verification and DKIM.
5. Open `IAM`.
6. Create a user for Aperture with programmatic access.
7. Attach SES permissions.
8. Put the access key and secret into `.env`.

### Important

New SES accounts often begin in the sandbox.
That means you can only send to verified recipients until AWS approves production access.

For a first smoke test, sandbox is fine.

## WhatsApp

## Recommended v1 choice

Use `Meta WhatsApp Cloud API` once you are past the first smoke test.

Use `Twilio WhatsApp Sandbox` only for the very first integration check if you want the easiest possible start.

Reason:
- Twilio is easier for first-day testing
- Meta Cloud API is usually cheaper in the long run because you avoid Twilio's extra per-message platform fee

This is an inference from Twilio's public pricing plus the fact that Meta Cloud API is the direct provider path.

### Twilio vars

- `APERTURE_TWILIO_ACCOUNT_SID`
- `APERTURE_TWILIO_AUTH_TOKEN`
- `APERTURE_TWILIO_WHATSAPP_FROM`

### Twilio setup

1. Create a Twilio account.
2. Open the console and copy your `Account SID` and `Auth Token`.
3. Enable the WhatsApp Sandbox.
4. Use the sandbox sender number for `APERTURE_TWILIO_WHATSAPP_FROM`.

### Meta Cloud API note

The current codebase is wired for Twilio right now, not direct Meta Cloud API.
If you want cheapest production WhatsApp, the next implementation step should be a `Meta Cloud API` adapter beside the existing Twilio adapter.

## OpenClaw

### Required vars

- `APERTURE_OPENCLAW_COMMAND`
- `APERTURE_OPENCLAW_CONFIG`
- `APERTURE_OPENCLAW_HOST_LABEL`
- workflow agent names, which can usually stay at defaults

### Setup flow

1. Install OpenClaw on the VPS.
2. Authenticate `openai-codex`.
3. Authenticate `github-copilot`.
4. Confirm:

```bash
openclaw models status --json
openclaw models status --check
```

5. Point `APERTURE_OPENCLAW_CONFIG` at the agency config path if you use a non-default config.

## Safety caps

These should stay low at the start:

- `APERTURE_EMAIL_DAILY_CAP=30`
- `APERTURE_WHATSAPP_DAILY_CAP=50`

Lower them further if you want a softer launch.
