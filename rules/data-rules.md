# Data Rules

## Models and Migrations

- Pair model changes with Alembic migrations when database schema changes.
- Keep enum values stable unless a migration and compatibility plan are included.
- Preserve dedupe keys for businesses, contacts, campaigns, and send attempts.

## Contact and Lead Data

- Use public business contacts only.
- Store source URLs or source records for evidence-backed contact discovery.
- Keep generated prospect lists and campaign exports under ignored `data/` paths unless the task explicitly asks for a checked-in fixture.

## Validation

- For model or migration changes, run relevant backend tests and include migration notes in the task summary.
