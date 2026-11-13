# Calling System Plan (CRM v2)

Date: 2026-11-13. Status: proposal only, no code written.
Code repo: https://github.com/dev-sanidhya/CRM (nested at `crm/app`). History and v1 decisions: [PLAN.md](PLAN.md).
Source of requirements: the Outbound Sales and Appointment-Setting Agreement (caller: Diksha, 70 dials/day minimum, 350/week, 80% = 280 warning line, 15% commission on attended-and-paid demos).

---

## 1. What the agreement actually asks the software to do

Every clause below turns into a hard requirement. Today the CRM covers almost none of them automatically.

| Clause | What it requires | Today |
|---|---|---|
| 3.1 / 3.3 | Count dials per day (70) and per week (350), adjusted for leave (-70), half day (-35), holidays | Counts every `call` activity, no week view, no leave |
| 3.2 | A dial = logged real attempt, same day. Same-number redial on the same day counts **only if the prospect asked for a callback** | Not enforced. Logging twice counts twice |
| 3.4 / 5.3 | Shortfalls caused by too few leads, tool or network failure must be reported same day and not counted against her | No way to record this |
| 3.6 | Honest numbers. Fake or inflated logs are grounds for termination | Nothing distinguishes a real attempt from a typed note |
| 4.1 | **No lead left hanging**: every conversation ends with a follow-up date/time, a booked demo, or a closing status | Optional. A call can be logged with no next step |
| 4.2 / 4.5 | Follow-ups first: overdue, then due today, then fresh prospects | Reminders and leads are separate pages; nothing orders the day |
| 4.3 | A Calling Playbook: attempts per lead, timing, fresh lead release, no-answer handling | Does not exist in the product |
| 4.4 | Do Not Call: mark immediately, never call again, respect India DND rules and calling windows | Only "Lost" stage, which does not block calling |
| 4.6 | End-of-Day Report: dials (new vs follow-up), conversations, demos with date/time, follow-ups done, due tomorrow, overdue with reason, complaints | Written by hand |
| 4.6 | Demo booked = lead details to the company the same day | No handoff, no alert |
| 5.1 / 5.2 | Weekly review: dials vs minimum, follow-up completion, demo quality. Two weeks under 80% within 4 weeks = repeated failure | No weekly view, no warning history |
| 6.2 to 6.5 | Commission only if: caller logged it, booked through the system, prospect **attended**, paid within **45 days**, on **net collected** revenue | No demo, attendance, payment or commission records |
| 6.5 | "The Company's lead register and call records decide" disputes | Caller can delete a sheet import, which cascades and **deletes call history** |

The theme: the CRM needs to become the system the contract points to. If the records are thin or deletable, every pay, warning, and commission conversation becomes an argument.

---

## 2. Findings in the current build

### Blocking right now
- **The Supabase project `lead-crm` (Mumbai) is paused.** Free tier pauses after a week without traffic, so the live CRM at aperturecrm.vercel.app cannot load data until it is restored. Free tier also has no backups. Since call records now decide pay and commission, this should move to Supabase Pro (about $25/month: no pausing, daily backups).
- **The schema is not in the repo.** Tables, RLS policies and the `import_leads` / `delete_sheet_import` RPCs live only in Supabase's migration history. One bad change and there is no version-controlled copy.

### Why the site feels slow (in order of impact)
1. **Server and database are on opposite sides of the world.** The Vercel project has no function region set, so it most likely runs in the default US East (Washington). The database is in Mumbai. Every query is a ~200 to 250 ms round trip, and pages make several in a row.
2. **Repeated, sequential round trips per page.** Each page load does: proxy `getUser()` (network call to Supabase Auth), layout `getUser()` + profile, then the page calls `getCurrentUserAndProfile()` again (not cached), then its own queries. The lead detail page awaits lead, activities, reminders, profiles one after another. That is 6 to 8 serial trips, roughly 1.5 to 2 seconds before anything renders.
3. **Stats are 9 separate count queries** on every "My Leads" load (`lib/callerStats.ts`), with `count: exact` over all-time history. The Team page multiplies that by the number of callers.
4. **The pipeline funnel downloads every lead row** to count stages in JavaScript (`getStageFunnel`). Fine at 260 leads, slow at 5,000.
5. **No optimistic UI.** Every click (done, snooze, log) waits for the server action, then a full re-render, both across the ocean.
6. **Three web fonts** (Fraunces variable with optical-size axis, Inter, JetBrains Mono) for an internal tool.

### Bugs and risks spotted
- `reminders/page.tsx` groups Overdue/Today/Upcoming with the server's local clock (UTC), not IST. Anything due between midnight and 5:30 am IST lands in the wrong bucket, and "today" starts at 5:30 am.
- Callers can delete a sheet import, which cascades through leads, activities and reminders. That erases the dial record the contract relies on.
- `stage` mixes two different ideas: where the deal is (pipeline) and what happened on the last call (disposition). That is why "Attempted" and "Contacted" exist but tell you nothing about what to do next.

---

## 3. The core idea: stop browsing leads, work a queue

At 70 to 110 dials a day the caller should never scroll a lead list to decide who to call. The system decides, the caller dials.

### 3.1 One-tap dispositions replace the activity form
Every dial ends with one tap (or one key) from a fixed list:

| Key | Disposition | Counts as dial | Conversation | Automatic next step (Playbook) |
|---|---|---|---|---|
| 1 | No answer | yes | no | next attempt per cadence |
| 2 | Busy / cut | yes | no | next attempt per cadence |
| 3 | Switched off / not reachable | yes | no | next attempt per cadence |
| 4 | Wrong number | yes | no | close lead (invalid) |
| 5 | Gatekeeper / ask for owner | yes | yes | callback at time given |
| 6 | Call back later (asked) | yes | yes | callback at the exact time given (same-day redial allowed and counted, per 3.2) |
| 7 | Interested, send details | yes | yes | WhatsApp/email details + follow-up in 2 days |
| 8 | Demo booked | yes | yes | demo record + founder alert + reminders |
| 9 | Not interested | yes | yes | close lead (lost), recycle in 90 days unless DNC |
| 0 | Do not call | yes | yes | close forever, phone blocked across all future imports |

Rules enforced by the system, not by memory:
- **A conversation cannot be saved without a next step** (clause 4.1). Choosing 5 or 6 opens a time picker with quick chips (In 2 hours, Tomorrow 11 am, Mon 4 pm). Choosing 8 opens the demo booker.
- **Dial counting follows clause 3.2 automatically.** A second dial to the same lead on the same day only counts if the previous disposition was "Call back later". The caller sees the counter tick or not tick, so there is nothing to dispute.
- **No-answers need zero typing.** About 60 to 75% of cold dials are non-connects. Those become one keystroke.
- Voice notes (already built) stay, attached to conversations only.

### 3.2 The Calling Playbook becomes settings, not a PDF
A founder-editable page that drives the queue:
- **Cadence for non-connects.** Default proposal: attempt 1 day 0, attempt 2 next day in the other half of the day (morning vs afternoon), attempt 3 day 3, attempt 4 day 7, attempt 5 day 14. After 5 non-connects: move to Nurture, recycle in 60 days. No same-day retries, because under 3.2 they would not count anyway.
- **Calling windows** (for example 10:00 to 19:00 IST, no Sundays). Leads are not offered outside the window, which also covers DND/TRAI hygiene.
- **Fresh lead release.** Each morning: fresh slots = daily target + buffer (default 70 + 30%) minus follow-ups due. If 30 follow-ups are due, about 61 fresh leads unlock. The rest stay in the pool, invisible. This is the main anti-clutter lever: the caller only ever sees today's work.
- **Priority.** Fresh leads are ordered by the sheet's score/priority, so the best prospects get called first.

### 3.3 The day, in order (matches clause 4.5)
The queue is built in this exact order and the UI shows it as sections:
1. Overdue follow-ups (with how late)
2. Callbacks with a fixed time (pinned, surfaced 5 minutes before)
3. Follow-ups due today
4. Fresh leads released today

Overdue items must carry a reason if they roll over at end of day, because the EOD report asks for it.

---

## 4. Caller features

1. **Call Mode (the main screen).** One lead at a time: business name, city, attempt number ("Attempt 3 of 5"), the pitch opener / hook / discovery question pulled to the top from the sheet's extra fields, the last 3 touches, and one big Call button. After the disposition, the next lead loads instantly (it is prefetched while she is on the current call). Keyboard: Enter to call, 1 to 0 for outcomes, N for voice note, S to skip with reason, / to search.
2. **Dial meter.** Always visible: dials today out of 70, split new vs follow-up, and pace ("on pace", "8 behind for 3 pm"). Weekly progress to 350 one click away, with leave already subtracted.
3. **Instant search (Cmd+K).** By name, city, or the last 4 digits of a phone number. Needed for inbound callbacks: "someone from 98xxx called back" should be one search.
4. **WhatsApp in one tap.** Approved message templates (intro, details after call, demo confirmation) opened as a `wa.me` link with the text prefilled. Free, manual send from her own WhatsApp, no Twilio involved.
5. **Blocker button.** "Not enough leads", "network down", "CRM down", "asked to do other work" with time stamps. Feeds clause 3.4 automatically so shortfalls are recorded the same day.
6. **End-of-Day Report in one click.** Generated from the logs with every field clause 4.6 asks for. She adds complaints/notes, presses Send, and it goes to the founders (WhatsApp text or email) and is stored. No more writing numbers by hand.
7. **Morning brief.** On first open of the day: "12 follow-ups due, 3 overdue, 2 fixed callbacks, 58 fresh leads released."
8. **Mobile layout that actually works for calling.** If she dials from her phone, Call Mode becomes a single column with a sticky bottom bar: Call, then the disposition sheet slides up after the call.

## 5. Founder features

1. **Today board (live).** Dials vs pace, connect rate, conversations, demos booked, overdue count, minutes since the last logged dial (idle signal), blockers raised. Refreshes live.
2. **Weekly scorecard per contract.** Dials vs 350 (adjusted for leave), percent of minimum, follow-up completion rate, EOD reports sent, demos booked vs attended. Auto-flags under 80% and keeps the warning history (clause 5.2: second week under 80% within 4 weeks is highlighted).
3. **Leave and holiday calendar.** Mark leave / half day / public holiday; targets adjust automatically.
4. **Demo pipeline.** Booked, then Attended / No-show / Rescheduled, then Proposal, Won, Paid. Each demo shows who booked it and when.
5. **Commission ledger.** For each won client: net collected amount (ex-GST, refunds), payment date, whether it is within 45 days of the attended demo, 15% commission, paid/unpaid, clawbacks. This is clause 6 as a table, so payouts are mechanical.
6. **Campaign (sheet) performance.** Per imported sheet: leads, % worked, connect rate, conversation rate, demo rate. This tells you which sheet sources and verticals to feed back into `ops/prospecting` scoring.
7. **Lead distribution.** Founder pulls go into a pool; assign in bulk by campaign or count. Ready for a second caller without redesign.
8. **Audit trail.** Who changed what and when. Nothing a caller does can delete call history; imports are archived, never cascade-deleted.

## 6. Demo booking (where commission is decided)

- Booking a demo picks a slot from the founders' Google Calendar free/busy, creates the event with a Meet link, and records `booked_by`.
- Instant alert to founders with the lead's full context (clause 4.6 handoff).
- Prospect gets a WhatsApp confirmation (template) and reminders: day before and 1 hour before. No-shows are the biggest leak, and attendance is what triggers commission, so reminders protect both sides.
- After the slot, the founder marks Attended / No-show in one tap. No-show automatically creates a reschedule task for the caller.

## 7. Keeping 110 dials a day uncluttered

Volume math: 110 dials a day is about 2,300 a month and several thousand leads in the system. What keeps that manageable:
- **The queue is the home screen.** The full lead list becomes a founder/search tool, not the caller's workspace.
- **Every lead is always in exactly one state:** Pool (not released), Active (has a next attempt), Scheduled (callback/follow-up at a time), Demo, Closed (won, lost, invalid, DNC), Nurture (recycle date). Closed and Nurture are hidden by default.
- **An integrity check runs nightly:** any open lead without a next step is flagged ("hanging leads: 3"), so clause 4.1 is enforced by the system.
- **Saved views** for the founder: by campaign, city, last disposition, attempt count, score.
- **DNC and dedup by phone across all imports.** A number marked DNC once is never offered again, whichever sheet it comes back in.

## 8. Architecture changes

### Data model (proposed)
- `call_attempts`: one row per dial. lead, caller, started_at (when Call was pressed), logged_at, disposition, connected, is_follow_up, attempt_number, counts_toward_minimum, note, voice transcript, later: duration and recording URL.
- `tasks` (replaces `reminders`): kind (callback, follow_up, demo_prep, reschedule), due_at, fixed_time flag, status, source rule, resolution.
- `leads` gains denormalised fields for fast queues: `state`, `next_action_at`, `attempt_count`, `last_disposition`, `last_contacted_at`, `campaign_id`, `recycle_at`, `is_dnc`. Partial index on `(assigned_to, next_action_at) where state is open`.
- `stage` becomes pipeline only: Prospect, Conversation, Demo booked, Demo attended, Proposal, Won, Lost.
- `campaigns` (from sheet imports, with release settings and archive instead of delete).
- `demos`, `payments`, `commissions`.
- `work_days` (per caller per date: working, leave, half, holiday, target, blockers).
- `eod_reports` (snapshot + sent_at), `playbook_settings`, `dnc_numbers`, `audit_log`.

### Server logic
- **One RPC per caller action.** `log_dial` inserts the attempt, applies counting rules, updates the lead, creates the next task, all in one round trip and one transaction. Same for `book_demo`, `get_queue`, `get_day_stats`, `get_week_scorecard`.
- **Stats from one query, not nine.** A single RPC (or a small daily rollup table) returns the whole dial meter and scorecard.
- **Migrations move into the repo** (`supabase/migrations`), so the schema is version-controlled and reviewable.

### Speed plan
| Fix | Expected effect |
|---|---|
| Set Vercel function region to Mumbai (`bom1`), next to the database | Each query drops from ~220 ms to ~5 to 10 ms |
| Verify the session locally (`getClaims()` with asymmetric JWT keys) instead of `getUser()` on every request; put role in the JWT; cache profile per request | Removes 2 to 3 network calls per page |
| Run independent queries in parallel; one RPC per page where possible | Pages render in one round trip |
| Optimistic UI on every disposition, done, snooze | Clicks feel instant |
| Prefetch the next lead in Call Mode | Zero wait between dials |
| Paginate activity history; funnel counts via SQL `group by` | Stays fast at 10x volume |
| One font family, self-hosted via `next/font` | Smaller first load |
| Supabase Pro (no pausing) | No cold or dead database |

Target: any screen under 300 ms from India, logging a dial feels instant.

Rough time saved: today a call takes about 60 to 90 seconds of admin (open lead from list, wait for a slow page, pick type, pick outcome, type a summary because it is required, separately add a reminder with a date picker, go back, find the next lead). With Call Mode, a non-connect is about 3 seconds and a conversation about 20 to 30 seconds with a voice note. At 70 dials with ~70% non-connects, that is roughly 45 to 60 minutes back per day, which is what makes 110 realistic.

## 9. UI direction

### What is wrong now
- The look is warm cream background + Fraunces serif headings + dark sidebar + green accent. That is the single most common generated-app style, and a display serif wastes space in a tool where density and numbers matter.
- Everything is a rounded white card with the same shadow, and small uppercase tracked labels sit above every block. The eye has nowhere to land.
- Primary work (who to call next) is not on any screen. The home screen is a paginated table of 30 leads.
- Forms are dropdown + Update button pairs. Each action is 2 to 4 clicks.

### Proposed direction: "Switchboard"
A working instrument, not a dashboard. Calm, dense, number-forward, built around one daily object: the 70-dial meter.

- **The one memorable element:** a full-width meter of 70 ticks across the top of every caller screen. Each logged dial fills a tick (ink for non-connect, green for conversation, blue for demo). By evening the bar is a picture of her day. The only animation in the product: a tick filling and the finished row sliding out of the queue when a disposition is logged.
- **Palette** (cool, functional, colour means status only):
  - Canvas `#EEF1F4` cool grey
  - Surface `#FFFFFF`
  - Ink `#1A2230` blue-black text and non-connect ticks
  - Muted `#5E6878`
  - Call green `#12805C` (Call button, conversations, used nowhere else)
  - Status: callback amber `#A86A12`, demo blue `#2851D6`, lost/DNC red `#B83A2A`
- **Type:** one family, IBM Plex Sans, with tabular figures for every number and phone, so columns of digits line up and the dial count never jitters. No display serif, no mono font.
- **Layout (desktop):**
```
+------------------------------------------------------------------+
| |||||||||||||||||||||||||||||||||||||||.......   41 of 70  on pace |
+---------------+--------------------------------------------------+
| Overdue    3  |  Studio Kadiwa                 Jaipur  Attempt 2/5|
| Callbacks  2  |  +91 98xxx xxx21          [ Call  Enter ] [ WA ]  |
| Due today 12  |                                                   |
| Fresh     58  |  Opener: Saw you run Meta ads for modular...      |
|               |  Discovery: Who handles your site enquiries?      |
| Up next       |                                                   |
|  Ark Interiors|  12 Nov 4:10 pm  No answer                        |
|  Nest Studio  |  11 Nov 11:30 am No answer                        |
|  ...          |                                                   |
|               |  1 No answer  2 Busy  3 Off  4 Wrong number       |
|               |  5 Gatekeeper 6 Call back 7 Send details          |
|               |  8 Demo booked 9 Not interested 0 Do not call     |
+---------------+--------------------------------------------------+
```
- **Mobile:** single column, the meter collapses to a thin bar, sticky bottom bar with Call; the disposition grid opens as a bottom sheet after the call.
- **Founder screens:** proper dense tables (40 px rows), sentence-case headings, no card-in-card, no uppercase eyebrow labels.
- **Copy:** buttons say exactly what happens ("Book demo", "Send report", "Mark attended").
- Quality floor: visible keyboard focus everywhere, works at 360 px wide, respects reduced motion.

## 10. Build order

**Phase 0: stabilise (about 1 day)**
Restore Supabase and move to Pro, set Vercel region to Mumbai, pull schema into `supabase/migrations`, stop callers from deleting imports (archive instead), fix the IST bug on Reminders, cache auth/profile per request.

**Phase 1: the calling loop (biggest win)**
Dispositions, `call_attempts`, Playbook settings, queue with fresh-lead release, Call Mode, dial meter with clause 3.2 counting, mandatory next step, DNC, Cmd+K search, new UI shell and design tokens.

**Phase 2: reporting and founder control**
EOD report one-click, blockers, leave calendar, weekly scorecard with warnings, live Today board, campaign performance, bulk assignment, audit log.

**Phase 3: demos to money**
Google Calendar booking, demo reminders, attended/no-show, payments, commission ledger, WhatsApp templates, nurture recycling.

**Optional later: telephony.** A click-to-call provider (for example Exotel or a similar Indian cloud telephony service) would log every dial automatically with duration and a recording. That removes manual dial logging, makes clause 3.6 (honest numbers) and 4.7 (recordings) automatic, and gives call duration for coaching. It has a per-minute cost, so it is worth it once the manual flow is proven.

## 11. Decisions needed from Sanidhya

1. Does the caller dial from her own mobile phone, from a laptop with a softphone, or both? This decides whether Call Mode is mobile-first.
2. Supabase Pro (about $25/month) approved?
3. Where should the EOD report and demo alerts land: WhatsApp, email, or Telegram?
4. Playbook numbers: 5 attempts over 14 days, calling window 10:00 to 19:00, fresh release = 70 + 30% buffer. Keep or change?
5. Demo booking against which calendar (Sanidhya's, Atharva's, or a shared one)?
6. Telephony integration now, or after Phase 2?
