# Calling System Plan (CRM v2)

Date: 2026-11-13 (revised same day). Status: proposal only, no code written.
Code repo: https://github.com/dev-sanidhya/CRM (nested at `crm/app`). History and v1 decisions: [PLAN.md](PLAN.md).
Context: one caller (Diksha) doing 70 dials a day, scaling to about 110.

## Decisions (Sanidhya, 2026-11-13)
- **No Calling Playbook** (cadence rules, release limits, settings page). Dropped for now.
- **Stay on Supabase free tier.**
- **The caller can delete calls and imports.** The agreement is strict on paper, but the team works on mutual trust, so the CRM should not police her.
- **Main focus: make logging calls into the CRM as fast and easy as possible.**
- Server moves to Mumbai.

---

## 1. Moving the server to Mumbai

The database is in Mumbai (`ap-south-1`). The Vercel project has no region set, so its server functions run in the default `iad1` (Washington, USA). Every database query crosses the world (~200 to 250 ms), and a page makes 6 to 8 of them in a row.

The free Hobby plan can choose any single region. Two ways, same result:

**Option A: dashboard (2 minutes)**
1. Vercel, project `aperturecrm`, Settings, Functions.
2. Function Region: pick **Mumbai, India (bom1)**. Save.
3. Deployments tab, latest production deployment, Redeploy. The region only applies to new deployments.

**Option B: in code (preferred, version-controlled)**
Add `vercel.json` to `crm/app`:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "regions": ["bom1"]
}
```
Push to main; the auto-deploy picks it up.

Expected effect: each query drops from ~220 ms to a few ms. Pages that take 1.5 to 2 s today should land in a few hundred ms. Combined with the code fixes in section 5 they become close to instant.

### Staying on the free tier safely
- The `lead-crm` Supabase project is **paused right now**. Restore it from the Supabase dashboard (project, Restore). Free, takes a few minutes.
- Free projects pause after 7 days with no activity. Normal weekdays keep it awake, but a week of leave or a holiday could pause it again. Free fix: a Vercel cron job (Hobby allows one run per day) that hits a tiny `/api/keepalive` route doing a single select.
- No automatic backups on free. Cheap safety net: a weekly export of leads and activities to CSV (a GitHub Action, or a "Download backup" button on the founder page).

---

## 2. Where the time goes today

To log one call, the caller currently:
1. Finds the lead in a paginated table of 30 (or searches).
2. Opens the lead page (slow: 1.5 to 2 s across the world).
3. Taps the phone number, makes the call, comes back.
4. Scrolls to the activity form, picks "Call" from a dropdown, picks "Answered / No answer" from a second dropdown.
5. **Has to type a summary** (the field is required, even for a no-answer).
6. Presses Log activity, waits for the server.
7. If a follow-up is needed, goes to a separate Reminders block, opens a date-time picker, types a note, presses Add, waits again.
8. If the stage changed, picks it from a third dropdown and presses Update, waits again.
9. Goes back to the list and finds the next lead.

That is roughly **60 to 90 seconds of admin per dial**, about 70 to 100 minutes a day at 70 dials. Around 60 to 75% of cold dials don't connect, and right now each of those still costs the full form.

---

## 3. The new logging flow: Call, come back, one tap

### 3.1 One "Today" screen replaces the leads list and the reminders page
The caller opens the CRM and sees one list, already in order:
1. **Callbacks** with a time (shown with the time; pinned at the top when they are due)
2. **Follow-ups due** today and overdue
3. **Not called yet** (fresh leads, highest score first)

Each row shows everything needed to decide, with no click-through: business, city, last outcome ("No answer, yesterday 4 pm"), number of tries, and the callback time if any. The full lead page still exists, but opens as a side panel over the list (no page change, no reload, no losing your place).

### 3.2 Calling and logging are one motion
1. She taps **Call** on a row. The CRM notes which lead and the time, then the phone dialer opens.
2. When she returns to the CRM after the call, **the outcome sheet opens by itself** for that lead. She never has to find the lead again or remember to log.
3. The app knows roughly how long she was away. A short gap (under about 25 seconds) puts "No answer" first; a long one puts the conversation outcomes first. It only reorders the buttons; she always chooses.
4. She taps one outcome:

| Outcome | Taps after the call | What happens automatically |
|---|---|---|
| No answer | 1 | Saved. Lead drops to the bottom and comes back in tomorrow's list |
| Busy / cut | 1 | Same as no answer |
| Switched off | 1 | Same as no answer |
| Wrong number | 1 | Lead closed as invalid |
| Not interested | 1 (+ optional reason chip) | Stage set to Lost, lead leaves the list |
| Do not call | 1 | Lead closed, number hidden from future imports |
| Call back | 2 (outcome + time chip) | Callback created at that time |
| Interested, send details | 2 (outcome + follow-up chip) | Follow-up created; one tap opens WhatsApp with the details message prefilled |
| Demo booked | 3 (outcome + day + time) | Stage set to Meeting booked, founders notified, demo reminder created |

5. A **5-second Undo** appears after every save instead of confirmation pop-ups. Mistakes are fixed with one tap, and any logged call can also be deleted later from the lead's history.

What she no longer does: pick a type, pick answered/unanswered, type a summary for no-answers, open a date picker, change the stage by hand, or go back to find the next lead. The outcome fills in all of those.

### 3.3 Time chips instead of date pickers
Callback and follow-up times are chips, not a calendar widget: **In 1 hour, This evening 6 pm, Tomorrow 11 am, Tomorrow 4 pm, Monday 11 am, Pick...** The chips adapt to the time of day (no "This evening" after 6 pm). Most callbacks become one tap.

### 3.4 Notes without typing
- **Quick note chips** for conversations: "Owner not available", "Asked for pricing", "Send portfolio on WhatsApp", "Already has an agency", "Budget issue", "Call in English/Hindi". Tapping adds the note text. The founders can edit the list.
- **Voice note** (already built, made lighter): hold the mic button on the outcome sheet and talk. The transcript becomes the note, and if she says a time ("call him Thursday at 4") it fills the callback chip. No separate confirm screen when it is only a note; the Undo toast covers mistakes.
- Typing is still there for anyone who wants it, never required.

### 3.5 On a laptop
If she works from a laptop as well, the same screen works with the keyboard: up/down to move between leads, Enter to open, number keys 1 to 9 for outcomes, T for time chips, V for voice. If she dials from her phone but logs on the laptop, the outcome sheet opens with "Log" instead of "Call", and the rest is identical.

### 3.6 Getting leads in, and adding one by hand
- Sheet pull and file upload already work; add drag-and-drop of a file anywhere on the Today screen.
- **Quick add**: a "+ Lead" box where she pastes or speaks "Nest Studio, Jaipur, 98xxxxxxxx". Useful for referrals and inbound callbacks.
- **Inbound callback**: search by the last 4 digits of a phone number, then log on the result directly.

### 3.7 Her day without extra work
- A small counter at the top: dials today (out of 70), conversations, demos. It updates the moment she taps an outcome, so she never counts.
- **End-of-day summary in one tap**: built from the day's logs (dials, conversations, demos with times, follow-ups done, callbacks due tomorrow). She adds a line if she wants and sends it to WhatsApp. No writing numbers by hand.

### 3.8 Expected time per dial

| | Today | New flow |
|---|---|---|
| No answer / busy / off | 60 to 90 s | about 2 s (one tap after returning) |
| Callback or follow-up | 90 s+ | 5 to 10 s |
| Conversation with a note | 2 min+ | 10 to 20 s with chips or voice |
| Finding the next lead | 5 to 10 s | 0 (next row is already highlighted) |

At 70 dials that is roughly **an hour or more back every day**, which is what makes 110 dials realistic.

---

## 4. Small data changes this needs
Kept minimal, no new subsystems:
- `activities`: add `outcome` (the list above) and `call_started_at`. `answered` gets filled from the outcome automatically.
- `leads`: add `last_outcome`, `last_called_at`, `attempt_count`, `next_call_at`. These are what the Today screen sorts and displays, so it is one fast query instead of joins.
- One simple built-in rule, no settings page: a non-connect sets `next_call_at` to tomorrow morning. Everything else comes from her taps.
- `reminders` stays as is for callbacks and follow-ups; the Today screen just reads it together with leads.
- One database function, `log_call(lead, outcome, note, callback_at)`, does the whole save (activity, lead update, callback, stage change) in a single round trip.
- Deleting a call removes its activity row and recalculates the lead's last outcome.

## 5. Speed fixes in the code
| Fix | Effect |
|---|---|
| Region `bom1` (section 1) | Each query from ~220 ms to a few ms |
| Check the login once per request (cache it) instead of 2 to 3 times; verify the session locally instead of calling Supabase Auth on every navigation | 2 to 3 fewer network trips per page |
| Run a page's queries in parallel; the Today screen as one query | Pages render after one trip |
| Optimistic saves: the row updates the moment she taps, the server catches up in the background | Logging feels instant |
| Replace the 9 separate stats queries with one | Counter loads instantly |
| Lead details as a side panel, prefetched for the next few rows | No waiting between calls |
| Stage funnel counted in the database, not by downloading all leads | Stays fast at thousands of leads |
| One font family instead of three | Lighter first load |

## 6. UI direction
Unchanged from the first draft, with the playbook parts removed:
- Drop the cream background, display serif and identical-card look (the most common generated-app style) for a calm, dense working screen.
- One font (IBM Plex Sans) with tabular figures so numbers and phone numbers line up.
- Colour only for meaning: green for Call and conversations, amber for callbacks, blue for demos, red for lost/do-not-call, everything else neutral.
- The one memorable element: the dial counter as a thin bar of 70 ticks across the top that fills as she logs. The only animation: a tick filling and the finished row sliding down the list.
- Mobile first for the Today screen and outcome sheet (big tap targets, sticky Call button), dense tables for founder screens.

```
+---------------------------------------------------------------+
| ||||||||||||||||||||||||||||||||.......  41 of 70   6 talks  1 demo |
+---------------------------------------------------------------+
| Callbacks                                                     |
|  Ark Interiors      Jaipur   Asked for pricing     4:00 pm [Call] |
| Follow-ups due                                                |
|  Nest Studio        Pune     No answer, yesterday  try 3   [Call] |
| Not called yet                                                |
|  Studio Kadiwa      Jaipur   score 82                     [Call] |
+---------------------------------------------------------------+

After returning from a call (bottom sheet on mobile):
+---------------------------------------------------------------+
| Studio Kadiwa  .  away 0:14                                   |
| [No answer] [Busy] [Switched off] [Wrong number]              |
| [Call back] [Interested] [Demo booked] [Not interested] [DNC] |
| (hold) mic   .  Owner not available  Asked for pricing ...     |
+---------------------------------------------------------------+
```

## 7. Build order
1. **Stabilise (about half a day):** restore Supabase, region `bom1`, keepalive cron, login caching, fix the Reminders page using UTC instead of IST for Today/Overdue.
2. **Logging flow:** outcome list, `log_call`, Today screen, auto-open outcome sheet after a call, time chips, note chips, Undo, optimistic saves, counter.
3. **Polish:** voice note on the outcome sheet, quick add, last-4-digit search, end-of-day summary, new visual design applied across founder pages.

## 8. Open question
Does she dial from her phone with the CRM open on the same phone, or dial from her phone while logging on a laptop? The flow supports both, but the first one gets the automatic "outcome sheet opens when you come back" behaviour, which is the biggest single time saver.

## Parked (not now)
Calling Playbook and cadence settings, fresh-lead release limits, Supabase Pro, delete restrictions and audit log, weekly scorecard with warnings, commission ledger, Google Calendar demo booking, telephony integration (auto-logged calls with recordings).
