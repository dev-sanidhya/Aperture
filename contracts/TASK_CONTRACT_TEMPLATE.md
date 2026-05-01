# Task Contract Template

Copy this file to `contracts/<task-name>_CONTRACT.md` and fill it before implementation for non-trivial work.

## 1) Task

- Title:
- Owner:
- Date:
- Scope:
- Out of scope:

## 2) Implementation Decisions

- Final approach:
- Alternatives considered:
- Dependencies impacted:

## 3) Acceptance Criteria

- [ ] Behavior criterion 1
- [ ] Behavior criterion 2
- [ ] Non-functional criterion, if any

## 4) Verification Commands

Run only relevant commands and mark results.

### Backend

- [ ] `python -m pytest backend\tests`

### Focused Tests

- [ ] `python -m pytest <targeted-test-file-or-node>`

### Scripts

- [ ] `python -m py_compile <changed-script>`
- [ ] Small smoke check:

### Website

- [ ] Manual HTML/CSS inspection:
- [ ] Screenshot evidence, if visual behavior changed:

## 5) Completion Record

- Summary of changes:
- Known risks:
- Follow-ups:
