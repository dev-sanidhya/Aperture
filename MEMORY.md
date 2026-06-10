# Aperture — Session Memory

Operators: Sanidhya + Atharva (co-run the agency). Founder name on all outreach = Atharva, company = Aperture Inc.

## Decisions
| Date | Decision | Why | What was rejected |
|------|----------|-----|-------------------|
| 2026-06-10 | Target US market, not India | Same cold-outreach effort to close; far higher payout; easier payments + deliverables | India SMB (low payout); used only as possible practice ground |
| 2026-06-10 | Vertical = US home services SMB (roofing, HVAC, water/fire restoration) | Closes the most clients: trivial ROI math, owner is decision-maker, huge TAM, underserved, battle-tested missed-call wedge | E-comm/SaaS (saturated/thin), generalist "anyone" positioning |
| 2026-06-10 | Segment = 20-250 Google reviews | Established, has budget, owner still reachable, fast 1-call close | Micro (<20, broke); mid-large/enterprise (gatekeepers, long cycles, diligence we can't pass yet) |
| 2026-06-10 | Wedge offer = missed-call-to-text-back + auto-booking, "free teardown" foot-in-door | One workflow + one number (recovered revenue) = sharp cold copy + obvious ROI | Generalist multi-service pitch |
| 2026-06-10 | Cold email primary channel; phone/SMS secondary | International => can't cold-call (timezone/screening); phone/SMS kept for no-email local leads | Cold-calling US from India as primary |
| 2026-06-10 | Lead source = Google Maps via Apify (NOT Apollo) | Apollo has weak local-contractor coverage; Maps is richest+cheapest for local home services | Apollo (reserved for upmarket/agency pivot) |
| 2026-06-10 | Email infra = dedicated secondary domains + warmed mailboxes | Personal Gmail / main domain => no auth, spam-flagged, suspension risk, kills site domain rep | Free @gmail accounts; sending from aperturecm.in |
| 2026-06-10 | Sequence SMB-first, then upmarket | Need case-study proof before larger clients' diligence; can't start at top cold | Starting at mid-large for bigger deal size |

## Current State (as of 2026-06-11)
- **Leads:** 433 ICP-filtered -> 400 w/ website, 428 w/ phone, 201 emails extracted, **183 verified valid**. Niches: roofing / HVAC / restoration. Metros: Dallas / Houston / Phoenix / Tampa. Total cost ~$5 (Apify scrape; email extraction + MX verify done free locally).
- **Email assets DONE:** 3-email sequence per lead (Day 1 / Day 4 follow-up / Day 9 breakup), Email 2 & 3 send as replies on the same thread. Opener personalized per lead (data-grounded on review count/city/niche, no fabrication). 33 distinct subjects, signature "Atharva / Aperture Inc.".
  - `leads_personalized.csv` — subject + opener cols, Instantly-ready
  - `email_drafts_full.md` — all 183 full sequences, ordered by company
- **NOT YET SENT.** Sending is the next step, gated on infra + a human spot-check.

## Blocked / Waiting On (all Atharva)
- Domain warmup (dedicated secondary domains) — the real bottleneck, 2-3 wk clock.
- Human spot-check of `email_drafts_full.md` — esp. flag generic/national catch-all addresses (e.g. `webmaster@`, `info@indiantypefoundry.com`, `info@ndiscovered.com`) to cut before send.
- Instantly/Smartlead setup + import + send.

## Open Questions
- Infra route: DIY Google Workspace vs done-for-you (Maildoso/Mailreef-style).
- Pricing for the wedge offer (setup fee + retainer) — not yet locked.
- Fix for the call-then-ghost problem (book next step on the call; qualify harder). Revisit after leads flow.

## Next Session Priorities
1. Confirm domains are set up + warming (2-3 wk clock — the bottleneck).
2. Human spot-check `email_drafts_full.md`; cut generic/national catch-all emails.
3. Set up Instantly/Smartlead, import `leads_personalized.csv`, map {{opener}} + {{subject}}, 20-25/day per mailbox.
4. Start phone/SMS channel on the ~250 phone-only leads (separate from email).
5. Scale lead gen: rerun scrape with new metros/niches once first batch validates.

## Session Logs
- 2026-06-10: Defined GTM strategy from scratch — market (US), vertical (home services SMB), wedge offer, channel, lead pipeline, email-infra rules. Set up the auditable decision loop (CLAUDE.md / MEMORY.md / ERRORS.md).
- 2026-06-10: Built + ran the lead pipeline. 433 ICP leads, 183 verified emails. Drafted 183 personalized openers via Haiku subagent, polished to 0 dupes.
- 2026-06-10 (cont.): Built full email assets. Rewrote bland Haiku subjects deterministically (`subjects.py`) into 33 distinct compelling lines grounded in review count/city/niche. Final assets: `leads_personalized.csv`, `email_drafts_full.md`.
- 2026-06-11: Onboarded both files (`email_drafts_full.md`, prior `MEMORY.md`) into this repo's canonical memory. Confirmed emails are drafted but NOT yet sent — sending is the next step.
