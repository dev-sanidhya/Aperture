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

## Next steps
<!-- Updated each session -->
