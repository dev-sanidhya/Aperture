# Deployment

## Recommended v1 topology

- 1 VPS
- PostgreSQL and Redis on the same box for testing
- Aperture API and workers as Python services
- OpenClaw as a separate service on the same host

This is the cheapest practical way to get a real end-to-end deployment running.
For the first live test, do not split the system across multiple machines.

## Best starter host

Use `AWS Lightsail`.

Why:
- the setup is simpler than raw EC2
- current Linux bundles include a `3 month free` offer on select plans
- you can resize later instead of migrating immediately
- SES is already in the AWS ecosystem

For Aperture, the safest testing target is:
- `2 GB RAM / 2 vCPU` if you want OpenClaw and browser work on the same box

You can try `1 GB RAM`, but OpenClaw plus browser automation will be tighter than I recommend.

## Services

- `postgres`
- `redis`
- `aperture-api`
- `aperture-worker`
- `aperture-openclaw`

## Boot order

1. PostgreSQL
2. Redis
3. OpenClaw
4. Aperture API
5. Aperture worker

## Health checks

- `GET /health`
- `GET /providers/openclaw`
- `openclaw models status --check`

## Initial host checklist

- create Lightsail instance
- open ports `22`, `80`, `443`, and `8080` temporarily for testing
- install system packages
- install Python `3.12+`
- install Node `22+`
- install `openclaw`
- authenticate OpenClaw with Codex and Copilot on the host
- install PostgreSQL and Redis
- clone repo
- create `.env`
- run Alembic migrations
- start API and worker
- smoke test provider health and Places ingestion

