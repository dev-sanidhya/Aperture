# Lead CRM — Plan

Status: Phases 1–3 built and pushed (2026-08-17), plus several rounds added
same-day beyond original scope: voice logging, a founder Team stats page
(§11), caller-side sheet pull/delete + search/pagination + a full visual
redesign (§12). Code repo: https://github.com/dev-sanidhya/CRM (nested at
`crm/app`). This folder holds the design/context docs that inform that repo.

Accounts live: founder `shishodiasanidhya@gmail.com`, shared founder
`info@aperturecm.in` (Sanidhya & Atharva), caller `diksha_aperture`.

## 1. The problem this solves

Today: leads live in Google Sheets. Founders and callers both look at the sheet,
but nothing tracks *who called whom, said what, and when to follow up*. Context
lives in people's heads or scattered WhatsApp/email threads. As lead volume goes
up, that breaks — callers forget follow-ups, founders can't see call history
without asking, and there's no single place that says "here's every lead and
where it stands."

What the CRM needs to do:
1. Be the system of record for lead **status + full history** (every call, note,
   email, reply).
2. **Remind** callers/founders when a lead needs a follow-up — automatically,
   not by memory, and visible as its own dedicated view, not buried in a lead
   list.
3. Pull leads in from Google Sheets **without manual re-entry or typing** —
   Sheets stays the place leads get *generated/scored* (by the existing
   `ops/prospecting/` pipeline), CRM becomes where they get *worked*. Since a
   **different sheet gets handed off each day**, this is a manual "paste the
   link, pull it in" action rather than one fixed sheet watched forever.
4. Let a caller **log a call by talking, not typing** — speak the summary of
   what happened, and the CRM turns that into a structured activity entry
   (and a reminder, if a follow-up was mentioned) automatically.
5. Feel like an Apple-designed tool to use — quiet, obvious, get-out-of-the-way
   — not like enterprise CRM software (see §3).
6. Be genuinely fast to build and cheap/simple to run — this is a 2-person
   (founder + caller) tool, not enterprise software. Avoid over-engineering.

## 2. Recommended stack (optimized for "fast to build, easy to deploy")

**Supabase (Postgres + Auth + instant REST/Realtime API + Edge Functions/cron)
+ Next.js frontend on Vercel.**

Why this over reusing the Agency repo's FastAPI/Postgres/Dramatiq stack:
- No backend boilerplate to write — Supabase generates the CRUD API from the
  Postgres schema directly (PostgREST). We only write Edge Functions for the
  Sheets-sync logic and reminder digests.
- Built-in Auth (email/password or magic link) covers "founder vs caller"
  login in ~zero code.
- Built-in Realtime means the lead list/kanban can update live across
  founder + caller screens with no polling code.
- Free tier is enough for this volume (a few hundred/thousand leads).
- Deploy story is trivial: `supabase db push` for schema, Vercel git-push
  deploy for frontend. No servers, no Docker, no Redis/Dramatiq to run.
- We already used Supabase successfully on the PriBhum Nest client project
  (see root [Plan.md](../Plan.md)), so the operational pattern is familiar.

Frontend: Next.js + Tailwind, deployed on Vercel. Mobile-friendly (caller may
work from a phone).

**AI model — decided: Groq.** Used for the voice structured-extraction step
(§6) — fast Llama-family inference, genuinely free tier, no card required.
Wired in as the one and only provider for now; not building a
multi-provider abstraction layer for a 2-person tool that has no reason to
switch providers on day one.

This is a deliberately different stack from the Agency backend (FastAPI/
Dramatiq) because the CRM's job — CRUD + auth + realtime + a cron sync — is
exactly what Supabase is built for, and pulling in Dramatiq/Redis here would
just be self-hosted plumbing we'd otherwise get for free.

## 3. Design language — Apple HIG-inspired

Goal: the CRM should feel like it disappears — the founder/caller should be
thinking about the *lead*, never about the *software*. Concretely, that
means borrowing from Apple's Human Interface Guidelines, not the
component-catalog SaaS-dashboard look:

- **Clarity over density.** One primary action per screen. The lead list
  shows what matters (name, stage, last touch, next reminder) and nothing
  else by default — everything campaign-specific (`extra_fields`, §4) is one
  tap away on the lead detail page, not crammed into the list as extra
  columns. Resist the urge to surface every field just because it exists.
- **Deference — content over chrome.** Minimal borders, minimal boxes-around-
  boxes. Generous whitespace instead of dividing lines to separate sections.
  Neutral background, a single accent color used sparingly (status/action
  only — not decoration). System font stack (San Francisco on Apple
  devices, falls back to system-ui elsewhere) rather than a "branded" font.
- **Depth through hierarchy, not decoration.** Subtle elevation (soft
  shadows, not hard borders) to show what's actionable vs. background —
  e.g. the reminder due *today* sits visually forward of ones due next week,
  without needing a label that says so.
- **Progressive disclosure.** Complexity is there when needed, invisible
  when not — e.g. the sheet column-mapping screen (§5) only ever appears
  the first time a new layout shows up, never as a permanent settings page
  you have to think about. The lead detail page opens to the essentials
  (contact info, current stage, latest activity) with full history a scroll
  away, not everything dumped at once.
- **One-tap over multi-step.** Every frequent action — mark a reminder
  done, change a lead's stage, confirm a voice-logged call — is a single
  tap/click with immediate visual feedback (the standard HIG pattern:
  direct manipulation, not "click, confirm in a modal, click again").
- **Consistent, restrained motion.** Short, purposeful transitions
  (a card settling into place, a reminder sliding out on complete) — never
  motion for its own sake, and always skippable/instant for anyone who
  wants speed over polish.
- **Practically**: Tailwind + a small set of primitives (card, list row,
  pill/badge for stage, button) reused everywhere rather than one-off
  styled components per screen — consistency is what makes an interface
  feel "abstracted away" rather than assembled from parts.

## 4. Data model (conceptual)

**leads** — based on the 5 example sheets reviewed (see §5a), which turned
out to have **4 distinct column layouts across campaigns/verticals**
(confirmed stable — no more layouts expected long-term), not one shared
schema. So the table has a solid fixed core plus a flexible bucket for
whatever varies:
- Fixed core: id, business_name, phone, city, website, stage (normalized —
  see §5a), assigned_to, created_at, updated_at, sheet_import_id (which pull
  brought this lead in — see `sheet_imports` below)
- `extra_fields` (jsonb) — everything campaign-specific that doesn't fit a
  fixed column: Hook Point, Offer Lane/Offer Angle, Personalization Fact,
  Pitch Angle, Segment, Reviews, Rating, Priority, Trigger, Discovery
  Question, Runs Ads, Pitch Opener/Pitch Script, and the sheet's raw
  Notes/Call-Status text. Nothing from a source sheet gets silently
  dropped just because it doesn't match a predefined column — it lands here
  and stays visible on the lead detail page even if it isn't queryable like
  a real column would be.
- score, if a given sheet includes one (not all do).

**stages** (pipeline): `New → Attempted → Contacted → Qualified → Meeting
Booked → Proposal Sent → Won / Lost`. Kept as a fixed enum on the CRM side
— see §5a for how each sheet's own status vocabulary maps into it.

**activities** (the "context" that bridges founder ↔ caller)
- id, lead_id, actor (who logged it), type (call / email / linkedin / note /
  status_change), summary, created_at
- source (`typed` / `voice`), and when voice: raw_transcript, audio_url
  (optional — keep the recording for playback, or discard after transcribing
  to save storage; a config choice, not a hard requirement)
- This is the timeline: every touchpoint on a lead in one feed, so a founder
  can open a lead and instantly see everything a caller has done without
  asking them.

**reminders**
- id, lead_id, assigned_to, due_at, note, status (pending/done/snoozed),
  source (`manual` / `rule` / `sheet_import` / `voice_extracted`)
- Created manually ("call back Thursday"), automatically by stage-change
  rules (see §7), extracted straight out of a voice note (§6), or pulled
  directly from a sheet that already has its own follow-up column (Layout D
  in §5a).
- This is its own top-level nav item, not a filtered view of leads — see §8.

**users**
- id, name, role (founder / caller), email — backed by Supabase Auth.

**sheet_imports**
- id, sheet_url, sheet_name/tab, imported_by, imported_at, column_mapping
  (jsonb), row_count, new_lead_count, updated_lead_count
- One row per "Pull" click — an audit trail of every day's import, and where
  the column-mapping-per-sheet-format gets remembered (see §5).

## 5. Google Sheets integration — manual "Pull" by link

Since a **different sheet gets handed off daily**, a background job watching
one fixed sheet ID doesn't fit. Instead:

**The Pull flow**
1. On the CRM, a "Pull from Sheet" button/field where you paste the day's
   Google Sheet URL (and optionally pick a tab if it has multiple).
2. Backend reads it via `https://docs.google.com/.../export?format=csv` —
   confirmed all 5 example sheets are publicly link-viewable, so no Google
   service-account/OAuth setup is needed for Pull.
3. **Column mapping — per header-signature, not global.** The 5 example
   sheets came in **4 distinct, now-confirmed-stable column layouts**
   (§5a) across campaigns/verticals. Mapping is saved keyed by the exact set
   of headers seen: the first time the CRM sees a given header signature, it
   shows the "map these columns → these fields" screen once; every future
   pull with that *same* header set is one click with zero setup. Since the
   4 layouts are confirmed as the long-term set, this is realistically a
   one-time setup done once per layout during Phase 1, not an ongoing task.
4. **Dedup on import — by phone, not email.** None of the 5 example sheets
   have an email column at all (§5a) — phone is the one field present in
   every layout, so it's the primary dedup key (normalized to E.164, which
   the sheets are already mostly using), with website domain as a secondary
   check when present. Re-pulling the same sheet, or a new sheet that
   repeats a lead, updates the existing lead instead of inserting a copy.
5. Every pull is logged in `sheet_imports` (§4) — so you can always see
   "what came in from which sheet, when," which matters once you're doing
   this daily across many sheets.
6. After a pull: a short summary ("14 new leads, 3 updated, 0 skipped as
   duplicates") so you know it worked without having to go check.

This is intentionally **on-demand, not scheduled** — a cron job polling a
sheet only makes sense when the sheet URL is stable, and here it isn't. If
that ever changes, a scheduled pull can be layered on top of the exact same
import logic with no rework — the Pull button is just a manually-triggered
instance of the same function.

**Direction of truth**: Sheets → CRM only. The sheet is the one-time input;
once pulled, the CRM owns status/notes/reminders and never writes back to
the sheet. Two-way sync is a much harder problem and not worth it here.

### 5a. What the 5 example sheets actually showed (confirmed stable, long-term)

Reviewed all 5 links directly (public CSV export). You've confirmed these
are the only 4 layouts and we'll build against this set for the long run —
no more layout discovery needed:

- *Layout A* (interior studios, metro/rating campaign): `Phone, Business
  Name, Metro, Reviews, Rating, Website, Runs Ads, Hook Point, Pitch
  Opener, Call Status, Notes`
- *Layout B* (interior studios, offer-lane campaign — sheets 2 and 4 were
  byte-for-byte the same layout): `Phone, Business Name, City, Website,
  Offer Lane, Offer Angle, Personalization Fact, Pitch Opener, Call
  Status, Notes`
- *Layout C* (clinics): `Phone, Clinic, City, Segment, Reviews, Rating,
  Website, Pitch Angle, Call Status, Notes`
- *Layout D* (design studios, priority-scored — sheet 5, the outlier):
  `Priority, Business, Phone, Segment, Trigger, Pitch Script, Discovery
  Question, Last Outcome, Next Action, Follow-up Date` — no Website
  column at all, and status/notes are split into `Last Outcome` /
  `Next Action` instead of `Call Status` / `Notes`.

Other findings that shape the build:
- **No email column anywhere** — dedup keys on phone (§5, step 4), not
  email.
- **Call-status vocabulary differs per layout** and needs normalizing into
  the CRM's fixed stage enum on import — e.g. `No Answer` / `Not Interested`
  / blank (Layout A/B), `Connected—Existing Solution` / `Gatekeeper` (Layout
  D). Small lookup table, one entry per distinct raw status string actually
  seen (roughly a dozen total across all 4 layouts) — build once, done.
- **Layout D's `Next Action` + `Follow-up Date` columns map straight onto
  the `reminders` table** — pulling that layout can auto-create a reminder
  per lead with no voice/LLM step needed, since the follow-up is already
  spelled out in the sheet.
- Common core across all 4 layouts: Phone, a business-name field (labeled
  differently — Business Name / Clinic / Business), a status field, and a
  notes-like field. Everything else is campaign-specific and goes into
  `leads.extra_fields` (§4) rather than forcing every layout into the same
  fixed columns.

## 6. Voice-first lead logging (the "just talk" flow) — BUILT

Status: shipped (2026-08-17). `src/components/VoiceLogger.tsx` + `src/lib/groq.ts`
+ `src/app/(app)/leads/[id]/voice-actions.ts`. Verified the exact production
prompt against Groq directly — correctly resolved "Thursday" to the right
date, defaulted time to 10:00, wrote a clean summary, stayed conservative on
`suggested_stage` (null rather than guessing) matching the confirm-first
design. Full mic-to-save loop untestable in the sandbox browser (no real
mic) — first live test happens when you or Diksha use it for a real call.

Goal: after a call, the caller taps **Record**, talks for 30–60 seconds the
way they'd naturally debrief a colleague ("Called Rahul at Kadiwa, he's
interested but wants a proposal by Friday, budget's tight so lead with the
cheaper tier, call him back Thursday"), taps stop — and the CRM fills in the
activity log, updates lead status if warranted, and creates a reminder, with
nothing typed.

**Pipeline — kept entirely free / no paid API keys required:**
1. **Capture + transcribe, in the browser, for $0**: use the browser's
   built-in **Web Speech API** (`SpeechRecognition`) instead of an audio-
   upload + Whisper/Deepgram round trip. This does mic → text conversion
   client-side — no audio ever leaves the browser, no API key, no per-minute
   cost, and it sidesteps Vercel's free-tier function limits entirely (10s
   execution / ~4.5MB body on Hobby) since there's no audio payload to send
   anywhere. Works well in Chrome/Edge/Android; worth confirming that's what
   the team actually uses day to day, since Safari/Firefox support is
   spottier.
2. **Extract structure — Groq (decided, §2).** Send just the resulting
   *text* transcript (a few hundred words — trivial payload) to Groq along
   with the lead's current context (name, stage, last few activities),
   asking for structured JSON:
   - `summary` (clean 1–2 line version of the call)
   - `suggested_stage` (if the conversation implies a status change —
     e.g. "he wants a proposal" → Proposal Sent-ish signal)
   - `follow_up` (date/time + note, if one was mentioned — parses "call him
     Thursday" into an actual due_at)
   - `sentiment`/`key_points` (optional, nice-to-have — interested / not
     interested / needs nurturing)
   Free tier, no card on file, fast inference — fits this workload
   comfortably. Not building a multi-provider abstraction for this; Groq is
   the one provider, swappable later only if it ever stops fitting.
3. **Confirm, don't auto-commit blind**: show the caller the extracted
   draft (summary + suggested stage + suggested reminder) for a one-tap
   confirm/edit before saving — this keeps trust high (nobody wants an LLM
   silently mis-hearing "not interested" as "interested" and no one catches
   it) while still being dramatically faster than typing the whole thing.
   Over time, once accuracy is proven out, auto-commit could be turned on for
   the low-risk fields (summary, activity log) while status changes and
   reminders always keep the one-tap confirm.
4. Save: writes an `activities` row (source=voice, transcript kept) +
   optionally a `reminders` row + optionally updates `leads.stage`.

This is the main lever on "not typing everything" — it turns a call debrief
into a 30-second voice note instead of a multi-field form.

## 7. Other automation

- **Auto-reminders on stage change**: e.g. moving a lead to "Contacted"
  auto-creates a reminder 3 days later ("follow up if no reply"); "Meeting
  Booked" auto-creates a reminder the day before. Rule table, not hardcoded —
  easy to tune without a redeploy.
- **Daily digest**: a scheduled job sends the founder + caller a daily
  summary (email, or WhatsApp/Slack if already in use) of: reminders due
  today, leads with no activity in N days, leads pulled in from yesterday's
  sheet. This is the main "bridge the communication gap" mechanism — founder
  sees caller activity without asking.
- **Score carry-through**: reuse the existing `ops/prospecting` scoring
  logic/output as-is (score column comes in via the sheet pull) rather than
  re-implementing scoring inside the CRM.

## 8. Reminders as a first-class, separate view

Not a filtered lead list — its own top-level page (own nav item, own
mobile-friendly layout):
- **Today / Overdue / Upcoming** grouping, across *all* leads, sorted by
  due time.
- Each reminder shows just enough lead context inline (company, stage, last
  activity snippet) to act without click-through, but links straight into
  the full lead detail if more context is needed.
- One-tap "Done" / "Snooze +1 day" / "Snooze to date" actions right on the
  reminder row.
- This is the page a caller opens first thing each day — effectively their
  to-do list, auto-populated by stage rules, sheet-imported follow-ups, and
  voice-extracted follow-ups (§6/§7) instead of hand-maintained.

## 9. Build phases

**Phase 1 — core**
- Supabase project + schema (leads, activities, reminders, users,
  sheet_imports)
- Manual Pull-by-link import flow (§5): paste URL → map columns (one-time
  per one of the 4 confirmed layouts) → dedup → insert/update
- Apple-HIG-inspired UI shell (§3): lead list, lead detail page (info +
  activity timeline + add-note/log-call form)
- Basic auth (founder/caller roles)

**Phase 2 — daily workflow**
- Kanban board by stage (drag to change status)
- Reminders as a separate top-level view (§8)
- Auto-reminder rules on stage change
- Daily digest (email first — simplest to stand up)

**Phase 3 — voice + polish**
- Voice-first call logging (§6): Web Speech API transcription (free,
  browser-side) → Groq structured extraction (free tier) → confirm → save.
  No paid API keys required for this to work end to end.
- Mobile-friendly caller view (voice logging matters most from a phone)
- Slack/WhatsApp digest instead of/alongside email, if that's where the team
  actually looks

Voice logging is placed in phase 3 not because it's low priority — it's the
biggest daily-friction win — but because it depends on the lead/activity/
reminder data model from phases 1–2 already existing to write into. Could be
pulled earlier if it turns out to matter more than the kanban/digest pieces.

## 10. Open questions to settle before Phase 1 starts

- Caller count today and expected at scale (affects whether per-caller
  assignment/permissions need to be strict or loose).
- Where should the daily digest land — email, WhatsApp, or Slack?
- Confirm caller/founder's day-to-day browser (Chrome/Edge/Android assumed)
  since Web Speech API's browser support is what makes voice logging free —
  if the team is on Safari/Firefox, the calculus changes and Whisper-style
  transcription becomes the fallback.

## 11. Founder team stats page — BUILT (2026-08-17, added beyond original plan)

Founder asked for per-caller visibility: how many calls a caller has dialled
(today + all-time), how many went unanswered, how many demos got booked, how
many follow-ups got completed, and the result of each one — all on one page.

**Schema additions** to support this (none of these existed before):
- `activities.answered` (boolean) — set on `type='call'` rows, both from the
  manual log-activity form (an Outcome dropdown that only appears when
  logging a Call) and from voice logging (Groq now also extracts
  `call_answered` from the transcript, shown as an editable field in the
  confirm-before-save draft).
- `activities.to_stage` — set on `type='status_change'` rows (both the
  manual stage-change form and voice-applied stage changes), so "demos
  booked" can be counted structurally (`to_stage = 'meeting_booked'`)
  instead of text-matching a summary string.
- `reminders.completed_at` + `reminders.resolution_note` — the Reminders
  page's "Done" button now expands inline into an optional one-line "what
  happened?" field before confirming, so completing a follow-up captures its
  outcome instead of just flipping a status flag.

**`/team` page** (founder-only, redirects callers back to their own leads):
one card per caller showing Today and All-time blocks (calls dialled, no
answer, demos booked, follow-ups done) plus a reverse-chronological
follow-up-results feed (lead name, what the reminder was for, the logged
result, when). "Today" is computed in IST regardless of server timezone
(`lib/timezone.ts`), consistent with the rest of the app's Asia/Kolkata date
formatting (`lib/format.ts`).

Verified end-to-end: logged an answered call, a no-answer call, and a
completed follow-up with a result note as the caller account, then confirmed
the founder's `/team` page showed the exact right numbers and feed entry,
and that the caller account is blocked from `/team` server-side.

## 12. Caller sheet pull/delete, search, and redesign — BUILT (2026-08-17)

**Sheet pull opened to callers.** Originally founder-only. The dedup-upsert
logic moved into a Postgres RPC (`import_leads`, security definer) so a
caller can pull a sheet without needing RLS visibility into every other
lead — one round trip instead of ~2 queries/row. A matching `delete_sheet_import`
RPC lets a caller delete a pull they made themselves (founders can delete
any pull) — removes every lead from that import plus their activities/
reminders via cascade, and the import record. Both RPCs self-guard on
`auth.uid()`.

Hit and fixed two real bugs during this: (1) `delete_sheet_import`'s
authorization check used `v_imported_by <> auth.uid()`, which is SQL NULL
(not TRUE) when unauthenticated — `if NULL` silently falls through as false
in plpgsql, so an anonymous caller could have bypassed the ownership check
entirely; fixed with an explicit `auth.uid() IS NULL` guard up front. (2) The
RPC's `insert into leads` never set `sheet_import_id`, so every delete
silently no-op'd on the leads themselves (only the import record vanished,
leads got orphaned) — caught by testing an actual pull-then-delete cycle
and checking row counts in the DB, not just the UI's success message.

**Search + pagination** on the leads list (`?q=`, `?page=`), backed by a
`pg_trgm` GIN index on `business_name` and `phone` for fast fuzzy matching
at scale instead of a sequential scan. 30 leads/page.

**New features:** click-to-call (`tel:` links on phone numbers, leads list
and lead detail), a "your day so far" stats widget on the caller's own
leads page (reuses `getCallerStats`), and on `/team`: an all-time combined
total across every caller plus a pipeline-by-stage funnel bar.

**Redesign:** root cause of the "annoying" look was `globals.css` hardcoding
`font-family: Arial, Helvetica, sans-serif` on `body`, silently overriding
the Geist font setup — the app had never actually rendered in the intended
font. Replaced with Manrope (body) + JetBrains Mono, added a proper indigo
accent color used sparingly for primary actions/active nav/focus rings
(Tailwind v4 `@theme inline` tokens), avatar initials in the sidebar,
active-link highlighting, and a full pass to zinc-based neutrals.

**A streaming attempt was tried and reverted**: wrapped each caller's
`/team` card in `<Suspense>` so cards would stream in independently. Worked
correctly per `next build`, but content only ever landed in a leftover
`<div id="S:0">` appended to `<body>` instead of being swapped into place —
Next.js's streaming-reveal script never completed in this specific sandboxed
test browser. Reverted to a plain blocking fetch (still fast — only 1-2
callers) rather than ship something unverifiable; confirmed working after
reverting. Worth retrying streaming later if the caller list grows enough
to matter, testing in a real browser rather than the sandbox.

Also created a second, shared founder account (`info@aperturecm.in`, name
"Sanidhya & Atharva") for both founders to log in with, alongside the
original individual founder account.

## Next steps
- Answer the open questions in §10.
- Deploy to Vercel when ready to move off local dev.
