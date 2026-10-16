# Agency - Plan

## What this repo is
The B2B agency lead-generation and outreach pipeline (FastAPI + Postgres + Redis + Dramatiq + OpenClaw).
Discovers agencies, scores them for AI-ROI fit, and generates founder-led outreach batches.

The marketing website was split out on 2026-06-10 into the nested `Aperture/` folder, which is now its
own git repo with its own memory. Nothing in this repo touches the website anymore.

## Clients
- **PriBhum Nest** (first agency client). Lives under `PriBhum Nest/` as two nested client git repos
  (gitignored here): `Mobile/` (github.com/wannabeaquant/pribhum-nest - Expo app + Supabase admin panel,
  Supabase phone/SMS OTP) and `Website/` (github.com/RajatMawal/PG-WEB - MERN PG-listing site with
  email OTP, JWT/Google auth).
  - 2026-06-22: Cloned both. On the Website repo, resolved leftover merge-conflict markers that were
    breaking the build (otpController, propertyController, Server.js), moved `redux/` into `src/`, and
    confirmed the existing email-OTP flow (register verification + forgot-password) is wired correctly -
    matching mobile's conceptual flow with minimum effort per client request. Work sits on the
    `feat/otp-flow-and-structure` branch in that repo; not pushed to the client remote yet.
  - 2026-07-01: Client asked to switch the Website OTP from email to SMS (matching mobile). Set up
    MSG91 as the SMS aggregator on the client's Jio DLT PE (PE ID 1201177304358511257): got a Service
    Inferred / Real Estate OTP content template approved (DLT template 1207178265665596727), created
    the MSG91 template (id 6a44a127714f8d640307b712), sender PRIBHU, authkey generated (ROTATE before
    prod - it was pasted in plaintext during setup).
    - Implemented SMS OTP on the Website using MSG91's **Flow API** (NOT the OTP API - the OTP API
      needs a literal ##OTP## variable which Jio DLT can't produce; Jio only offers {#number#}). We
      generate/store/verify the 6-digit code ourselves in the Mongo `Otp` collection (keyed by phone)
      and send via Flow API filling the ##number## variable. Files: Server/Controller/msg91.js (new),
      otpController.js, userController.js (forgotPassword/otpVerify/updatePassword now phone-based),
      Model/Otp.js (+phone); Client register-OTP + forgot-password pages now take a 10-digit phone.
    - Root-caused the delivery blocker through 3 layers: (1) MSG91 OTP API doesn't work with Jio DLT
      templates at all (needs literal ##OTP##, Jio only offers {#number#}) -> switched to Flow API;
      (2) template stuck "Pending"/"Failed - PE-TM chain error on DLT" because the client's Jio DLT PE
      had ZERO registered telemarketer chain -> created chain linking PE 1201177304358511257 to MSG91's
      TM id 1302157225275643280 (Jio DLT: My Telemarketers > Create New Chain), approved after ~4 days;
      (3) MSG91 account needed KYC completion before real (non-demo) sends worked. Once chain hit
      "Registered" on DLT and template re-verified to "Verified by DLT" on MSG91, delivery confirmed
      working end-to-end (2026-07-10, live SMS received on 9368322072).
    - 2026-07-10: Extended the same working MSG91 setup to the **Mobile** app, replacing its
      never-actually-wired `EXPO_PUBLIC_MOCK` flag (dead code, deleted - mobile's real sign-in already
      used Supabase phone OTP, it just had no real SMS delivery configured). Rewrote
      `Mobile/supabase/functions/send-sms-otp/index.ts` (Supabase's "Send SMS" auth hook) to call MSG91's
      Flow API with the same authkey/template/sender as the Website. Wired `[auth.hook.send_sms]` +
      `[functions.send-sms-otp] verify_jwt = false` in supabase/config.toml, secrets via
      supabase/functions/.env. Confirmed real SMS delivery via local Supabase (`supabase start`) hitting
      `/auth/v1/otp` for 9368322072.
      Gotchas hit getting local Supabase Send-SMS hooks working (useful if this breaks again):
      `Buffer` isn't a global in the Deno edge runtime -- needs `import { Buffer } from 'node:buffer'`;
      GoTrue's hook call has no JWT, so the target function needs `verify_jwt = false` or every call
      500s with "Hook requires authorization token"; the edge-runtime container caches a compiled
      bundle and does NOT hot-reload on file edits -- always `supabase stop` + `supabase start` (not a
      bare `docker restart` of just the edge-runtime container, which leaves Kong's proxy pointing at a
      dead instance and every hook call hangs ~30s before a 502).
    - Both Website and Mobile changes are uncommitted in their working trees (client repos) -
      not pushed per instruction. Rotate the MSG91 authkey before production launch (pasted in
      plaintext chat during setup).
  - 2026-07-10 (same day, continued): client asked to take Mobile to production and get a demo APK
    to the PriBhum Nest owner for review.
    - **Fixed a real rendering bug**: SignUpScreen's PG Owner / Student role cards rendered as tiny
      ~100px unstyled boxes instead of filling their row. Root cause in `mobile/src/components/ui.tsx`'s
      `PressableScale`: the `style` prop (incl. `flex:1`) landed on an inner `Animated.View`, not the
      outer `Pressable` — which is the actual flex item inside a `flexDirection:row` parent, so it
      shrink-wrapped to content instead of stretching. Fixed via
      `Animated.createAnimatedComponent(Pressable)` so style+transform both land on the real flex item.
      This was a repo-wide bug (affects every `PressableScale` user with a flex layout, not just
      SignUpScreen). Verified via Expo web preview + DOM layout measurements (screenshot tool was
      flaky/timing out in this session, used computed-style/bounding-rect eval instead).
    - **Created a real hosted Supabase project** (org "Dehshat", project `pribhum-nest`,
      id `ojnuhuzeuhitraufdtpk`, region ap-south-1, free tier / $0mo) via the Supabase MCP + CLI — the
      mobile app previously only worked against local Docker Supabase (127.0.0.1), which is useless in
      an APK installed on someone else's phone. Pushed all 6 migrations, deployed `send-sms-otp` with
      `verify_jwt=false`, set real secrets (`supabase secrets set`, needed a client-generated Personal
      Access Token since the MCP server's own OAuth session isn't reusable by the CLI), and pushed
      `[auth.hook.send_sms]` config via `supabase config push` (had to temporarily swap the hook URI
      from the local `host.docker.internal` address to the real `https://ojnuhuzeuhitraufdtpk...`
      one for the push, then revert locally after — `config push` is a one-time snapshot, not a live
      sync). Hit and fixed two gotchas: `storage.vector.enabled=true` 402s on free tier (unused
      feature, disabled); `secrets = "env(SEND_SMS_HOOK_SECRET)"` in config.toml silently resolves to
      empty if that env var isn't exported in the exact shell that runs `config push`, causing "Hook
      requires authorization token" on the hosted project even though the function itself is correctly
      `verify_jwt=false`. Confirmed a real SMS delivered end-to-end from the hosted backend
      (9368322072). Seeded realistic demo data via the repo's existing `supabase/demo_seed.sql`
      (owner "Rajesh Kumar", 5 PGs across Bangalore/Pune/Noida, 28 beds/14 free, photos) directly
      against the hosted DB.
    - **Built a release APK locally** (no EAS/Expo account, $0 cost): `expo prebuild --platform
      android`, then `gradlew assembleRelease` (release build type uses the debug signing config by
      default in Expo's template, so no separate keystore needed for a demo/sideload APK). Set
      `app.json` package to `com.pribhumnest.app` (was defaulting to a placeholder
      `com.ssanidhya.mobile`). `.env.production` (hosted URL/anon key, gitignored) is what
      `NODE_ENV=production gradlew assembleRelease` bundles — confirmed by grepping the built APK's JS
      bundle for the hosted project ref. Hit a Windows-only native-build failure: deeply nested project
      path (`...PriBhum Nest\Mobile\mobile\android\...`) plus CMake/Ninja's own long-path handling
      (independent of the `LongPathsEnabled` registry key, which was already on) pushed C++ object
      file paths over 260 chars for `react-native-safe-area-context`/`react-native-screens`. Fixed by
      building through a short-path Windows directory junction (`C:\Users\<user>\pbn` ->
      `...\Mobile\mobile`, junction removed after build) instead of touching the real project location
      or Gradle internals. Final APK: 78MB, package `com.pribhumnest.app`, minSdk 24, at
      `mobile/android/app/build/outputs/apk/release/app-release.apk`.
    - Not yet done / flagged for the client: rotate the MSG91 authkey (still the one pasted in this
      chat) before real launch; the Supabase Personal Access Token the client generated for CLI access
      should be revoked once no longer needed; MSG91 AuthKey IP restriction was left off for dev
      convenience, tighten before wide launch.
  - 2026-07-10 (same day, continued): **created a real hosted Supabase project** for Mobile (org
    "Dehshat", project `pribhum-nest`, id `ojnuhuzeuhitraufdtpk`, region ap-south-1, free tier) since the
    app previously only worked against local Docker Supabase — useless in an APK on someone else's
    phone. Pushed all 6 migrations, deployed `send-sms-otp` with real secrets (needed a client-generated
    Supabase Personal Access Token since the MCP server's own OAuth session isn't reusable by the CLI),
    pushed `[auth.hook.send_sms]` config (temporarily swapping the hook URI from
    `host.docker.internal` to the real hosted URL for the push, then reverting locally — `config push`
    is a one-time snapshot, not a live sync). Seeded demo data via the repo's own `demo_seed.sql`
    (owner "Rajesh Kumar", 5 PGs across Bangalore/Pune/Noida). Confirmed a real SMS delivered end-to-end
    from the hosted backend.
  - 2026-07-10 (continued): user reported the demo APK crashed on open ("bug in the app"). Root-caused
    by installing it on a local Android emulator (Android SDK + a JDK were already present on this
    machine, so no device/cloud build service needed) and reading `adb logcat` crash traces directly —
    much faster than guessing. This became a long chain of missing-global crashes, each fixed only to
    reveal the next, because **this was literally the first-ever release/Hermes build of this app** —
    dev-mode Expo Go never exercises this code path. Root causes found, in order:
    1. `FormData`, `Headers/fetch/Request/Response`, `Blob`, `URL/URLSearchParams`, `WebSocket`,
       `File/FileReader` are all normally installed *lazily* by React Native's own `setUpXHR.js` via a
       getter-based `polyfillGlobal()`. That lazy mechanism doesn't resolve in time in this build —
       Supabase's client chain and even Expo's own fetch wrapper reference these globals eagerly at
       their own module-init time, crashing with "Property X doesn't exist" / "expected globalThis.X to
       be installed".
    2. `globalThis` itself isn't reliably aliased to `global` early enough — fixed by explicitly setting
       `global.globalThis = global` first.
    3. `AbortController`/`AbortSignal` aren't part of RN's polyfill set at all. The obvious fix
       (`abort-controller` npm package, already a transitive dep) is a trap: Metro resolves its
       `browser` field over `main`, and that file assumes `self`/`window` exist (`typeof self !==
       'undefined' ? self : ...`) — neither exists in RN, so it throws immediately on import. Fixed
       with a ~20-line dependency-free polyfill class instead. (RN's own `setUpXHR.js` sidesteps this
       exact trap by deep-importing `abort-controller/dist/abort-controller` directly, bypassing
       package.json field resolution — good precedent, didn't need to duplicate it once we had our own
       polyfill.)
    4. `global.performance` doesn't exist; RN's performance logger falls back to `global.performance
       .now()` when no native QPL timestamp module is present, crashing during `renderApplication`.
       Fixed with a trivial `{ now: () => Date.now() }` stub.
    - **Debugging methodology note** (useful if this class of bug recurs): checking "is my code in the
      bundle" via `grep` on the APK's `assets/index.android.bundle` is **unreliable and produced a false
      negative that wasted significant time** — that file is compiled Hermes bytecode, and grep matches
      inside its string-constant pool can produce misleading coincidental substring concatenations (a
      real example hit this session: "ZZZDIAG" + "Generator is already executing" concatenated into a
      false-positive-looking "ZZZDIAGenerator..." match). The only reliable way to inspect what's really
      in a Hermes release bundle is a real sourcemap: Gradle writes one to
      `android/app/build/generated/sourcemaps/react/release/index.android.bundle.map`; resolve a crash's
      `line:column` with the (old-API, synchronous) `source-map` npm package:
      `new (require('source-map').SourceMapConsumer)(mapJson).originalPositionFor({line, column})`.
    - Also relevant: **ES `import` statements are hoisted above regular top-level statements**
      regardless of textual source position, and Babel/Metro preserve the *relative order* of hoisted
      imports. A plain `require()` call sitting inside a top-level `if` block in `index.ts` runs too
      late if anything hoisted above it (e.g. `import App from './App'`, whose transitive chain reaches
      `src/lib/supabase.ts`'s eager `createClient()` call) needs the polyfill first. Fix: the polyfill
      file itself must be imported via `import './polyfills'` as literally the first import, not
      `require()`d conditionally.
    - Final state: `mobile/polyfills.ts` (new) holds all of the above, imported first in `index.ts`.
      Verified crash-free via a real local Android emulator (Android SDK's `emulator`/`adb`, no EAS/cloud
      device needed) — app launches, renders the Welcome screen, stays alive. Rebuilt APK is at
      `mobile/android/app/build/outputs/apk/release/app-release.apk`; not yet re-verified against the
      hosted Supabase OTP flow on-device (was verified via curl against the hosted project earlier in
      the day, and the app code itself is unchanged since then — only startup polyfills changed).

## Pipeline (high level)
1. `ops/prospecting/discover_agencies.py` - discover candidate agencies (seed list or web-search fanout).
2. `ops/prospecting/build_agency_pipeline.py` - score sites, optional capped OpenClaw enrichment on top leads.
3. Outreach batch generation - founder-led LinkedIn / email (Amazon SES in production only).

## Key constraints
- OpenClaw enrichment OFF by default; only `--openclaw-top-n` for top leads.
- Min score threshold 45 before outreach generation.
- Twilio WhatsApp only after explicit compliance checks.
- Amazon SES only in production, never for testing.
- Generated prospect CSVs go to `data/prospects/` (gitignored).

## Lower-tier cold-call lead scrape (2026-06-22)
Goal: scrape NET-NEW lower-tier leads (weak/no website, modest reviews, but earning -- the opposite
of the established tier-2 firms in the user's existing `vapi_contacts.csv` / `india_call_list_personalized.csv`).
Targets: 200 US roofing (voice agent), 100 India interior, 150 India aesthetic clinics.
- Tool: Apify `compass/crawler-google-places` (Google Maps Scraper). User's OWN Apify token (FREE plan,
  $5/mo hard cap) -- this is the binding constraint, not actor choice. ~$5 per 1,000 places.
- Strategy: search smaller suburbs/localities (so small operators rank top, not the giants).
- User decisions: India market for interior+clinics; same 4 metros for roofing (deduped); Maps number +
  E.164 format check (no carrier validation); STRICT low-tier = weak/no/http website ONLY, partial counts
  accepted (won't blow the $5 cap to hit full targets).
- Scripts (ops/prospecting/): `scrape_lower_tier.py` (initial), `scrape_gaps.py` (curl run-sync gap fill),
  `consolidate_recover.py` (classify Apify datasets by searchString -> raw buckets),
  `build_lists.py` (strict filter + phone validation + dedup vs existing -> final CSVs).
- Gotchas hit: FREE 8GB memory cap (async runs orphaned by a dead poller piled up -> 402); Python urllib
  timeouts in this env (use curl instead); Windows cp1252 decode bug on UTF-8 names (fetch via `curl -o`,
  not Python text mode). Apify keeps every run's dataset server-side, so partial/failed local saves are
  always recoverable by re-fetching the dataset id.
- RESULT after India top-up (`scrape_more_india.py`, fresh BLR/DEL/GGN localities; usage ~$4.46 of $5):
  us_roofing_lower_tier.csv = 97, india_interior_lower_tier.csv = 67, india_aesthetic_clinics_lower_tier.csv = 36.
  All E.164-valid, unique, 0 overlap with existing lists. Budget now effectively exhausted ($0.54 left).
  Clinics inherently low yield under strict filter (Indian clinics nearly all have own sites).
- Clinic budget-max pass (`clinic_blast.py` + cheap actor `S3TUPOWUK8RoocPjh` @ $1/1k via
  `normalize_cheap.py`): premium actor blocked once remaining < its per-run reservation, so switched to
  the $1/1k actor for the last cents. CONFIRMED the FREE cap is a hard $5 (not $7) -- Apify error
  `not-enough-usage-to-run-paid-actor`. Usage maxed at ~$4.97/$5.
- FINAL counts: us_roofing_lower_tier.csv = 96, india_interior_lower_tier.csv = 67,
  india_aesthetic_clinics_lower_tier.csv = 42 (now spans BLR/DEL/GGN + Pune/Noida/Mumbai). 205 total,
  all E.164-valid, unique, 0 overlap with existing lists.
- To go further: FREE $5/mo is fully spent -> user must raise the Apify cap / use a funded token.
  Free rebuild/re-tune from already-paid Apify datasets: re-fetch dataset ids -> consolidate_recover.py
  (+ normalize_cheap.py for cheap-actor data) -> build_lists.py. Loosen is_lower_tier() for more volume.

## Lead CRM (2026-08-17, planning only)
Started planning a CRM to replace/augment the current Google Sheets lead
workflow as volume grows — needs to store per-lead context (call notes,
history), auto-remind on follow-ups, and bridge the founder/caller
communication gap. Sheets stays the source leads get generated/scored into
(existing `ops/prospecting/` pipeline); CRM becomes where they get worked.
Sync direction: Sheets -> CRM only (scheduled pull + optional Apps Script
push later), not two-way. Recommended stack: Supabase (Postgres/Auth/
Realtime/Edge Functions+cron) + Next.js on Vercel — deliberately not the
Agency backend's FastAPI/Dramatiq stack, since Supabase gives CRUD+auth+
realtime+cron for free instead of hand-building it. Code will live in a
separate repo: https://github.com/dev-sanidhya/CRM. Full design doc:
[crm/PLAN.md](crm/PLAN.md).

## Next steps
- CRM: answer open questions in crm/PLAN.md §7 (sheet column layout, caller
  count, digest channel, stable row key), then scaffold the Supabase +
  Next.js app in the dev-sanidhya/CRM repo.
<!-- Updated each session -->

## CH+ 3D site: V3 video regeneration (2026-10-02)
- Approach: drive Google Flow via Claude in Chrome (browser MCP at PORTFOLIO/tools/google-flow-browser-mcp was reviewed, Linux-only, not used).
- Prompts: chplus-3d-rebrand/PROMPTS_V3_TRANSFORMATION.md (locked villa bible + 6 legs). Working files in chplus-3d-rebrand/flow-v3/ (gitignored).
- Flow account has too few credits for Veo Quality (100/clip). Using Veo 3.1 Fast (20/clip), which cannot Extend, so each leg starts from the previous leg's last frame (ffmpeg -sseof extract, upload as start frame).
- Leg 0 done: Veo cut from empty plot to finished villa at ~4.5s (no gradual build, no orbit). Villa and car look good; last frame is a clean front view. Decision pending on keeping it.
- Next: legs 1-5 from last frames, strip audio, encode (GOP 8, faststart), wire into index.html; CONTACT US via HTML overlay if Veo misspells.
- Leg 1 done (flow-v3/leg1.mp4): villa+car, through driver window into POV, drives to portico. Last frame saved as leg1_last.png. Flow's video-viewer "Save frame" icon makes a project image asset usable as next start frame (no file upload needed; Flow upload button exposes no file input to the Chrome extension).
- BLOCKER: Flow credits exhausted for Fast (20). Only one Lite clip (10) affordable. Legs 2-4 (exit car + enter, interior, card/CONTACT US) need a credit top-up by the user.

## Lead Funnel demo (lead-funnel/, 2026-10-02)
- What: AI qualification funnel for a client who gets Meta-ad enquiries. Telegram agent qualifies or disqualifies against a minimum-budget bar and files leads into a central CRM as Active / Nurtured / Disqualified / Needs human. Built as a trust-layer demo. Full docs: lead-funnel/README.md.
- Stack: Node 22+, zero npm deps (node:sqlite), Telegram long polling, Cloudflare Workers AI (Llama 3.3 70B, fallback gpt-oss-120b) via its OpenAI-compatible endpoint.
- Why Telegram: Meta only allows DMs after the customer messages first, so cold-DMing a Google Form lead on Instagram is not allowed; Telegram deep link (t.me/bot?start=token) mimics a Click-to-DM ad.
- Key decisions: the LLM only extracts facts and phrases replies; src/qualify.js (pure code) decides the category, so the budget bar is exact and explainable. Inbox/outbox pattern in SQLite for crash safety, per-lead serial queue, rolling summary for context, hallucinated-budget guards.
- Demo features: admin console (pipeline board, lead drawer with manual takeover, what-if budget slider, designers with auto-assignment, follow-up fast-forward, webhook CRM sync, CSV), persona simulator (10 personas, 10/10 pass), in-browser test chat as Telegram backup, hosted enquiry form + Google Form Apps Script.
- State: 25 tests pass; live simulator 10/10. Cloudflare creds are in lead-funnel/.env (gitignored). NOT yet tested against a real Telegram bot (needs a BotFather token).
- Next: user creates bot via @BotFather and sets TELEGRAM_BOT_TOKEN; expose via cloudflared and set PUBLIC_URL for the Google Form script; rehearse with /reset; record a backup screen capture; confirm the client's real project types, min budget and designers and replace the Aperture Interiors placeholder content in Settings.

## Lead Funnel: calls, reminders, UI revamp (2026-10-03)
- Problem found in real use: the customer said "tomorrow 5 pm" for the designer call, the bot confirmed, but the CRM captured nothing. Treated as a class of problem: any important fact the customer states must become structured data.
- Fix: structured call time (when.js parser cross-checks the LLM, business timezone), plus property/scope/style/best-time/phone capture, designer brief, call-booked team alerts, phone requested together with call time (Instagram gives no phone).
- Follow-ups: assistant reminds before the call while the messaging window is open; otherwise the lead lands in a red "Needs you now" column (attention.js is the single source of truth) for manual follow-up. Owner actions: done with note, snooze, reschedule.
- UI: admin console rewritten in plain language (Today, Leads board with Needs you now column, Calls agenda, Try it, Practice, Settings), responsive, dark mode.
- State: 46 tests pass; live simulator still matches expectations; deployed repo: github.com/dev-sanidhya/AI-Funnel.
- Next: confirm with the client which extra details designers want captured; consider WhatsApp as a second Meta channel (templates allow first contact); move off the ngrok URL to a stable host.

## Glad U Came demo video (lead-funnel/demo-video/, 2026-10-05)
- What: ~90s premium product film for the client Glad U Came (Mumbai PR and influencer agency, IG @instagladucame, mint brand colour). Flow: title card, Meta ad, self-filling lead form, Instagram DM chat with Aria while a live lead profile fills, zoom out into the Lead Desk CRM, new lead lands on the board, drawer walkthrough (summary, next step, details, call, chat), recap of Today / Leads / Calls / Rules, outro.
- Stack: Remotion 4 (React, frame-exact, deterministic), Inter + Instrument Serif, no screen recording. All data is fictional (Riya Mehta, Mira Skin, Ananya Rao). The CRM scenes are a faithful recreation of the product's design language in client mint, with PR/influencer data, not a capture of the live app (the live app is still interior-design specific in its field labels).
- Two cuts from one codebase: Film (1920x1080) and FilmVertical (1080x1920) with a native phone layout of the CRM, because 16:9 is unreadable on a phone held upright. Shared timeline in src/timeline.js (scene starts, chat script, sound cues).
- Audio: synthesized in Python (scripts/make_audio.py): ambient score plus UI sounds synced to cues.json, normalised to about -15 LUFS. soundtrack.wav is gitignored and regenerable (node scripts/dump-cues.mjs && python scripts/make_audio.py).
- Render: from demo-video/, npx remotion render src/index.jsx Film|FilmVertical out/x.mp4 --port=3411 --props='{"fps":30}' (port 3000 is the funnel server, so pass a different port). Output in out/ is gitignored.
- Decision: user considered replacing the ad opener with a reply to an organic post (client does not run Meta ads), then chose to keep the ad flow as is. If revisited: the DM would start with Aria answering a comment, and comment-triggered DMs need the Instagram comments webhook, which the funnel does not subscribe to yet (story replies and DMs already work).
- Next: final 60fps renders of both cuts, user review, possible tweak of copy and handle.

## Demo data reset (2026-10-07)
- Wiped all leads, messages and activity from the live funnel DB and seeded 18 sample leads with scripts/seed-demo.js (lead-funnel). Backup of the previous DB: lead-funnel/data/backup-before-demo-seed.db (gitignored). Settings, designers and channel tokens were kept.
- Sample leads cover every stage (New 1, In conversation 2, Active 9, Needs a person 2, Nurture 2, Not a fit 2) and every "Needs you now" state (call soon, call overdue, no call time, no phone, asked for a person, waiting for reply, AI had trouble, follow up by hand), a manually pinned stage, a completed call with notes, both channels (Instagram, Telegram) and all three designers.
- Safety: leads with meta.demo use the no-op transport (replies from the console show as sent, nothing reaches a real account) and background timers skip them unless "Run follow-ups now" is pressed.
- Product fix: nextStepFor now says "Call done..." once a call is marked done (was "Confirm a call time").
- Re-run anytime: node scripts/seed-demo.js --wipe (times are relative to now, so re-run before each demo).

## Arty chatbot integrated into the Interio Arty website (verify/, 2026-10-07)
- What: the production chatbot from interioarty-chatbot (not the older interioarty-demo prototype, which has no streaming, memory or summaries) is now live in verify/ (clone of namdevjedgule/InterioArty). Mock chat widget, its fragment, CSS and JS removed; js/chatbot.js loads on all 29 pages.
- Pipeline kept intact: SSE streaming, 12-message window, sticky knownLead memory, rolling summary every 8 turns, mandatory-details gate (name, contact, city, budget), re-ask validator, em dash filter, lead summary, WhatsApp/call handoff, persona and business facts in config/.
- Changes vs source: widget re-themed to emerald/gold/Montserrat; city extraction now accepts natural replies ("Kharadi, Pune. Budget around 18 lakh"), which previously never qualified a lead while the bot still said the closing line; budget hint trimmed; spaced en dash stripped; chips hidden after reload mid-chat. The city fix is NOT yet back-ported to interioarty-chatbot.
- Verified in browser: greeting from /api/meta, streamed replies, memory across reload and across pages, lead saved with AI summary, mobile layout. Deterministic smoke tests pass; live Groq tests hit provider rate limits when run back to back.
- Open: leads live only in the visitor's localStorage (no studio-side delivery); needs a webhook or CRM call in handleLead. Local commits only, not pushed (not the user's repo). Local preview: launch.json entry interioarty-site (port 3010).
- Next: decide lead delivery (webhook, email or CRM), back-port the city fix, then deploy on Vercel with GROQ_API_KEY.

## Decision: verify/ is the delivery (2026-10-07)
- The user chose verify/ (full stack inside the client repo namdevjedgule/InterioArty) as the single deliverable. The lighter alternative (InterioArty-site/, widget wired to the hosted backend) was discarded and its folder and preview entry removed.
- Fixed in verify/ (local commits 49cfb58, 26f7205): a bare "area" in the assistant's question made a flat-size answer ("Two bedroom hall") get stored as the city. The trigger now only fires on city, location, locality, neighbourhood, "which/what area" or "where is/are ...". Regression cases added to verify/scripts/smoke.js; suite passes.
- verify/ is 6 commits ahead of origin/main and not pushed (client's repo, so push or PR only with the user's go-ahead).
- interioarty-chatbot (837b2b0) has its own city fix (lead-ins, "Baner, Pune") but not verify/'s one-sentence "city and budget" case; verify/ lacks the comma-preserving format. Merge only if the two repos should stay in sync.
- Still open: leads exist only in the visitor's browser (no studio-side delivery); production backend at interioarty-studio.vercel.app needs a manual redeploy to pick up 837b2b0.

## verify/ squashed to one commit and tested locally (2026-10-07)
- verify/ (clone of namdevjedgule/InterioArty) is now ONE local commit, f44cf92 "feat(chat): add Arty AI chatbot", on top of origin/main. Not pushed (client's repo, push or PR only on the user's go-ahead). Old interioarty-chatbot repo is unchanged since 837b2b0.
- Tested running verify/ locally: 121 smoke checks pass, a full 47-message conversation passes (no repeat-asks, no truncation, name, phone, email, city and budget kept, CRM name, phone, size, budget and location correct), and real-browser runs on the site check greeting, memory, the four-field gate, no dashes and the CRM record.
- Fixed in verify/ while testing: (1) flat-size answers stored as the city (bare "area" trigger); (2) non-answers ("I don't know", "undecided", "my flat") stored as the city, and "around Baner" dropped; (3) iPhone curly apostrophes made "I'm Rajesh" invisible so the bot re-asked the name; (4) spaced en dash filter ran per streamed chunk and missed split dashes, now runs on the buffer (stripDashes in api/lib/streaming.js); (5) a network error reaching Groq returned HTTP 500, now retries and degrades to the polite busy reply (callGroq in api/chat.js); (6) a question that only mentions a place ("Do you only work in Pune?") was stored as the visitor's city. Each has a regression test in verify/scripts/smoke.js.
- The long-convo-test now answers whatever the bot asks (name, contact, city, budget) instead of fixed replies, checks repeats only against the bot's question sentences, and compares the CRM location field.
- interioarty-chatbot does NOT have fixes 1 to 6 (verify/ is the only place). The live backend at interioarty-studio.vercel.app has the old behaviour.
- Open: studio-side lead delivery (leads only live in the visitor's browser, verify/ has no crm.html), pushing verify/, and the site's own titles and copy still say "InterioArty".

## CRM page added to verify/ (2026-10-07)
- verify/ had no CRM page. Ported crm.html + js/crm.js from interioarty-chatbot, restyled to the site theme (emerald/gold, Playfair/Montserrat), noindex, "Back to site" link, Avg. Reply Time stat dropped.
- Wired the same way as the chatbot repo: the widget already writes to localStorage `interioarty_leads` and posts on BroadcastChannel `interioarty-leads`, and crm.js reads both. Open /crm.html in the same browser to see leads.
- Verified in browser with a seeded lead (summary, spec chips, transcript, status button, WhatsApp). Folded into the single verify/ commit (amended, still unpushed).
- Limitation unchanged: store is per-browser, so the studio only sees leads from the browser they open /crm.html in. Real delivery needs a webhook/DB.

## Lead delivery backend + admin panel in verify/ (2026-10-07)
- Replaced the browser-only CRM (crm.html/crm.js, removed) with a server-side flow: widget POSTs each qualified lead to /api/leads (public, write-only, validated, capped, per-IP limited), stored in Upstash Redis (REST, no deps) or .data/leads.json locally. On Vercel without Redis it returns storage_not_configured instead of losing data.
- Admin: /admin.html + js/admin.js. Password (ADMIN_PASSWORD env) gives a signed HttpOnly SameSite=Strict cookie (7 days; changing the password signs everyone out). Endpoints: /api/admin/session (login/logout/check), /api/admin/leads (GET/PATCH status+notes/DELETE). Features: stats, filters, search, status dropdown, notes, Call/WhatsApp/Email, CSV, 20s refresh.
- Widget: stable per-lead cid (UUID), full conversation log (MAX_LOG 300, separate from the 30-message model history), chained ordered syncs with retries, re-sync after each reply and after the AI summary. Server merge never blanks known fields and never lets visitors touch status/notes.
- Tests: npm run test:leads (offline, 50+ checks incl. auth, forged/expired cookies, rate limit, Redis mock). Real-browser check: chat -> lead synced with full transcript + summary -> admin login from fresh state -> status/notes saved.
- Owner TODO on Vercel: add Upstash Redis integration, set ADMIN_PASSWORD, redeploy, open /admin.html.
- Limits: rate limits are per warm instance; single shared password (no per-user accounts).

- Pushed verify/ (single commit f5ec4e5) to namdevjedgule/InterioArty as branch Chatbot-Integration (2026-10-07). main untouched. PR not opened yet.

## Lead Funnel on Vercel (2026-10-10)
- Live at https://aperture-lead-funnel.vercel.app (admin /admin, form /form, IG webhook /webhook/instagram). Code: https://github.com/dev-sanidhya/Lead-Funnel (folder lead-funnel, source in `core/`, Vercel entry `api/index.js`).
- Database: Supabase Postgres project `aperture-lead-funnel` (ap-south-1), app role `funnel_app` via the transaction pooler, RLS on with no policies. Local dev still uses SQLite when DATABASE_URL is empty. The whole store is async with two drivers (core/db.js).
- Follow-ups rebuilt: pure planner `core/followups.js` decides the next action per lead (nudges, call reminder, stall/hand-over, form lead who never opened the chat, nurture check-ins). Rules: Instagram 24h window (last nudge pulled inside it), quiet hours 9pm-9am IST, counters restart when the customer replies, sends are claimed with compare-and-swap so overlapping runs send once.
- Scheduler: pg_cron job `funnel-tick` calls /api/cron every minute with the CRON_SECRET bearer (Vercel Hobby cron is daily only, a daily Vercel cron stays as backstop). Per-lead DB lease replaces in-process locks; background work goes through waitUntil.
- Verified on prod: cron tick, follow-up, call reminder and form-lead hand-over all fired exactly once on test leads (deleted afterwards).
- Next: point Meta webhook callback at the Vercel URL (needs dashboard login), real DM test from @ssanidhya29_, then move to the client's own Instagram account.

## Funnel update: calendar booking, 8h nudge (2026-10-10)
- Follow-up defaults: first nudge after 8h, next after 12h more (last one always lands inside the IG 24h window), quiet hours OFF by default (settings still allow them). Production DB settings updated to match.
- Calendar booking (core/calendar.js): Google Calendar via a free service account (env GOOGLE_SERVICE_ACCOUNT_JSON, owner shares calendar with its e-mail, "Make changes to events"). Aria offers real free slots, checks any time the customer names against freebusy, offers 3 alternatives when busy, accepts "the second one", books the event, moves/deletes it when the owner reschedules in the admin. Demo/sim leads never touch the calendar; a Google outage never blocks the chat. Admin: Connect tab > Calendar card with a Test button.
- Status: code tested with a fake Google (85 tests pass) and deployed. NOT yet live: needs the service account JSON from Google Cloud (free) and the owner's calendar shared with it.
- Meta webhook now points at https://aperture-lead-funnel.vercel.app/webhook/instagram (saved in the dashboard).

## Chat memory hardening (2026-10-10)
- Instagram has no limit on conversation length. Our memory: contiguous context (all messages not yet summarised, min 14, max 40, no gap with the rolling summary), summary refreshed when 6+ messages overflow the window (CAS-protected), plus an append-only `meta.memory` list of every concrete detail the customer states (extracted per turn, shown in the lead drawer as "Details they shared").
- Guards: recall/confirmation questions ("did I say...?") can no longer edit stored data (facts.js early return); replies cannot state money or counts (clients, years, awards) that are not in the business facts or the customer's own details (validator.js); sentence splitter no longer breaks decimals like 6.5 lakh.
- Tests: test/memory.test.js (no-gap over 60 messages, summarizer down, bounds) + live check `node scripts/memory-eval.js` against the real model: 11/11 (recall after 68 messages, false-premise corrections, no invented prices/numbers/celebrities, budget unchanged).
- Calendar auth idea: Composio managed OAuth as alternative to the service account; decision pending (see chat).


## Aperture website redesign direction (2026-10-15)
- User finds the Aperture site (Aperture/website) not premium; refs: capxai, Apple. Wants Remotion in the hero.
- No code changed. Concept artifact published: https://claude.ai/artifact/D7BStrVNTWnpBt1nPHr73c
- Direction: darkroom palette (obsidian, graphite, bone, amber used only as light), Instrument Sans + Instrument Serif italic + JetBrains Mono, white pill buttons, one iris hero as a Remotion composition, one bone-white band for rhythm.
- Next: user picks direction; then port tokens, hero (Remotion Player), bento, other pages.

- Round 2 (2026-10-15): user rejected the amber/iris concept as too AI-ish. Studied Refero DESIGN.md (Apple dark: black canvas, 600 weight, 28px panels, pills, no shadows, one accent) and capx.ai (measured: #08080A, 54px display -0.048em, mono uppercase labels, 4px radii). Built a from-scratch concept: white/gray bands + black theater panel, Geist + Geist Mono, signal orange only for automated state, Remotion-style "Teardown" film (38.5h -> 2.0h). Artifact: https://claude.ai/artifact/XVP7XD9DcnKuRfJGRvSvof

## Aperture site rebuild (aperture-site/) - 2026-10-15
- New standalone Next.js 15 project in aperture-site/ (port 3100, preview entry "aperture-site" in .claude/launch.json). Old Aperture/website untouched. NOT committed or pushed (user instruction).
- Direction v1 (ink and paper editorial, serif, single tone, text-heavy, scripted agent replays) was REJECTED by the user. Deleted entirely, including the fake call/QA/trace replays.
- Direction v2 (current): Virgil Abloh / Off-White language. White, black, industrial orange, tape yellow, cobalt. Archivo 900 uppercase + IBM Plex Mono captions, quotation-mark type, hazard tape marquee, zip ties, barcodes, FIG captions, crosshair cursor. Posters per client with one big number. Copy kept very short and rewritten (not the deck wording).
- Pages: / , /work, /work/[slug] (5 case pages), /services, /studio, /contact. Agentic parts kept: Ask Aperture concierge (retrieval over lib/data.ts chunks, quotes only, refuses off-site questions) and Ctrl+K command menu. Contact scope tag composes a mailto, stores nothing.
- Facts come from Aperture_Client_Work_v2.pptx. Discrepancies to confirm with founders before launch: Persuaders is a 30-day trial / in progress in repo docs; CapxAI is NDA-sensitive and marked in progress in the Glad U Came deck; PriBhum has 9 migration files vs 6 in deck; InterioArty 9 lead fields not found in code; BPO numbers are a planning model (labelled on site).
- Next: confirm the claims above, add real screenshots/video per client if available, set up Vercel project, replace Aperture/website when approved.

### Iteration 2 (2026-10-15, aperture-site)
- Hero mark kept black (user preference); hero headline now "AI SYSTEMS FOR REAL WORK". Posters now show client name + one plain sentence (no stat numbers); each client has its own page (what we built, from the old clients page and deck). 12 clients incl. FirstQA, RSVD, Luminar, ROCCS, OWASP, CH Plus Partners, LiveDelite, InterioArty. Copy rewritten in plain sentences. Skipped for now: Owra Khanna (agreement sent, not delivered) and AIGTM Channel (partner channel, not a client). To confirm: CH Plus and LiveDelite client status, OWASP trademark use. Still not committed or pushed.

### Contact redesign (2026-10-15, aperture-site)
- mailto form removed. New /contact: two WhatsApp/call cards (Atharva +91 99900 52074, Sanidhya +91 93683 22072) as the main path, a 3-step AI-assisted quick brief (Intake.tsx), email as a quiet fallback, optional booking card when NEXT_PUBLIC_BOOKING_URL is set. Ask Aperture assistant now offers WhatsApp/brief buttons on pricing or contact intent.
- API: app/api/assist (restates the need and maps to our services via Groq if GROQ_API_KEY, else keyword fallback; never quotes prices) and app/api/lead (honeypot, rate limit, validates contact, notifies via ntfy/Telegram/Resend). With no notifier configured it returns not_delivered and the UI falls back to a prefilled WhatsApp message so no lead is lost.
- TODO to go live: set env vars in Vercel (see aperture-site/.env.example): NTFY_TOPIC or TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_IDS, RESEND_API_KEY + LEAD_EMAIL_TO, GROQ_API_KEY, optional NEXT_PUBLIC_BOOKING_URL (Cal.com link). Footer headline still undecided.

### Pushed to GitHub (2026-10-16)
- New site pushed to wannabeaquant/Aperture main as a normal (non-force) commit 5e8cb4d "feat(website): rebuild site with AI intake": website/ folder replaced with the Next.js app; rest of repo untouched. Root vercel.json now has a fail-safe build command so a project still using the old static settings fails (keeping the previous live deploy) instead of serving a broken site.
- That repo's Vercel project is not in the dev-sanidhya Vercel team (the visible "aperture" project tracks dev-sanidhya/Aperture and its builds are ERROR). Owner of the wannabeaquant Vercel project must set Root Directory = website and add env vars (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS, optional GROQ_API_KEY, NEXT_PUBLIC_BOOKING_URL, NTFY_TOPIC, RESEND_*). Rotate the Telegram token (it was pasted in chat).
- 2026-10-16: AI step switched from Groq to Cloudflare Workers AI (CF_ACCOUNT_ID, CF_API_TOKEN, optional CF_AI_MODEL; OpenAI-compatible endpoint, same as lead-funnel). Pushed to wannabeaquant/Aperture main as 66f4478. First Vercel deploy failed, most likely the intentional root vercel.json guard until Root Directory = website is set in that Vercel project (not visible from our Vercel teams). Atharva edited README.md on main at 00:22 (no conflict).
- 2026-10-16: vercel.json fixed (legacy builds: website/package.json via @vercel/next, route /(.*) -> /website/$1) and pushed as 0514070; could not fully verify routing locally (Windows symlink EPERM at last build step; Docker off). If Vercel still fails, set Root Directory = website. Real logos added locally: OWASP (owasp.org SVG, recolored black), CH+partners (chpluspartners.com PNG, watermark removed), InterioArty (verify/images/logo), AIGTM wordmark (typeset, matches their own site/decks). LiveDelite logo not found online, still typeset. Commit "feat(website): add real client logos" is ready in scratchpad clone, NOT pushed yet.
- 2026-10-16: pushed 4df88b9 (real client logos) and 9145948 (Vellar client #14 + LiveDelite logo) to wannabeaquant/Aperture main, normal commits. Vercel deploy of the legacy-builds vercel.json still needs confirming by the project owner.
- 2026-10-16: pushed 1f47180 (hybrid AI chat: /api/chat on Cloudflare Workers AI, grounded in lib/data.ts chunks, numbered citations, no model call when nothing relevant) and e2464ac (transparent light/dark favicon + apple icon) to wannabeaquant/Aperture main. aperturecm.in still 404 until Vercel Root Directory = website is set in the wannabeaquant Vercel project (legacy builds config in root vercel.json served 404). website/vercel.json forces nextjs preset.
- 2026-10-16: pushed 19b837d "smarter chat and scroll fix": chat leads with speed + quality, typical timelines (automations 2-3 days, websites 4-5 days, multi-agent under a week; voice agents/apps not stated so deferred to founders), answers general questions without citations, cites site only when used, no competitor comparisons. Smooth-scroll (Lenis) opted out inside chat + Ctrl K via data-lenis-prevent; page locked behind the dialog. Still waiting on Vercel Root Directory = website in the wannabeaquant project.

## Interioarty second client account (2026-10-16)
- Separate deployment, same code: https://interioarty-funnel.vercel.app (Vercel project interioarty-funnel). Own Postgres schema `interioarty` (role interio_app, RLS on, cannot see Aperture tables), own admin password, own pg_cron job `interioarty-tick`, own Instagram token. Shared: the Meta app, Cloudflare/Groq keys.
- One Meta webhook address serves both accounts: Aperture's deployment forwards events for account 17841406990794509 (interioarty) to Interioarty's, and each deployment drops events for accounts that are not its own (INSTAGRAM_ACCOUNT_ID, INSTAGRAM_FORWARD). Aperture behaviour unchanged (emoji/tone settings default off).
- Persona: Arty, built from interioarty-chatbot/config (business.js, personas.js) via scripts/client-interioarty.js. emojis 'light' (alternate messages, one tasteful emoji, mid-message or end, none when declining) and polish on (no filler, no brochure clichés). No qualification bar (min_budget 0, no timeline cut-off): the bot chats and fills the inbox, stage is only a label.
- Lead Inbox: the website CRM page (crm.html) is now served at /crm on the Interioarty deployment, backed by the database. Instagram, website chatbot (widget posts to /api/crm/ingest, wired in interioarty-chatbot index.html) and form leads land in one inbox; status new/contacted/closed saved. Lead Desk (/admin) remains for the team.
- Open: real DM test from @ssanidhya29_ to @interioarty; Meta app review (Advanced Access) before ordinary customers' DMs are delivered; delete the junk test lead in Interioarty's inbox; Facebook Page and WhatsApp channels still to build.

## Photos (2026-10-16)
- Customers' Instagram photos are downloaded (Meta image hosts only, 4 MB cap), described by Cloudflare's Mistral Small 3.1 vision model (works without a licence click; ~950 tokens, ~31 neurons per photo; fails over across both CF accounts), stored in the new `media` table (BYTEA, per-schema, RLS on) and passed into the chat as "[Photo] <description>" so replies, memory and the summary all know what it showed. If vision fails the photo is still kept and the assistant asks what it shows.
- Display: Lead Inbox (/crm) and the console lead view show the actual image inline (served from /api/media/:id, staff login required) with the description as caption. Companion/empty events and hearts are ignored (earlier phone-number incident).
- Not done yet: voice notes (could be transcribed with Whisper), videos, other attachment types still get the polite "cannot open attachments" reply.

## Photo storage moved to Supabase Storage (2026-10-16)
- Photos no longer fill the 500 MB database: they go to Supabase Storage (1 GB, separate), one bucket per client (`interioarty-photos`, `aperture-photos`). Only the public (anon) key is used, with an insert-only rule on a strict name pattern <lead id>/<32 hex>.<ext>, 4 MB and image-type limits per bucket. Verified live: the key cannot list, overwrite, delete or read through the API; files open only by their random address, which stays server-side (the CRM asks /api/media/:id, staff login required, the app fetches the file).
- Fallback: if storage is off or refuses an upload, the photo is kept in the database (media.data), so none is lost. media.storage_path holds the path otherwise.
- Known limit: deleting a lead does not delete its files from storage (the public key cannot delete). They are tiny and unreachable; clean up later with a service key if needed. One 130 KB test file (999/...jpg) sits in interioarty-photos.
