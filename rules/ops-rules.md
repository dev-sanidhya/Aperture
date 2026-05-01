# Ops Rules

## Local Runtime

- Do not commit `.env`, virtualenvs, caches, generated data, local OpenClaw state, or provider credentials.
- Keep `.env.example` and setup docs current when configuration changes.
- Preserve Windows scripts under `ops/windows/` unless replacing them with documented alternatives.

## Deployment

- Update deployment docs when runtime commands, provider setup, environment variables, or process topology changes.
- Keep production send paths auditable and reversible.

## Prospecting Scripts

- Generated prospect outputs belong under ignored `data/` paths.
- Seed examples can be committed when they are public URLs and useful for reproducible smoke tests.
- Prefer smoke checks that do not require large network runs.
