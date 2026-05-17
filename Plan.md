# Aperture — Plan

## What this repo is
Two parts in one repo:
1. **`website/`** — Aperture's public marketing site (HTML/CSS/JS, 4 pages: index, services, process, contact). This is the sales surface for the agency (Sanidhya + Atharva).
2. **`backend/`, `openclaw/`, `ops/`, `contracts/`** — the B2B agency lead pipeline (FastAPI + Postgres + Redis + Dramatiq + OpenClaw) that powers prospecting and outreach. Unrelated to the website refactor below.

## Current session — Website visual refactor (2026-05-17)

### Goal
User asked for a Web3-style, abstract, motion-heavy refactor of the entire website UI. No content changes — visuals + motion only. Premium feel justifying Aperture as a sharp tech agency.

### Approach
Stayed inside the existing vanilla HTML/CSS/JS stack (no framework rewrite). The lift goes into:

- **New design system** (`assets/styles.css`)
  - Color tokens swapped from warm cream/gold to dark obsidian + holographic violet (`#b794ff`), cyan (`#5ee7df`), pink (`#ff79c6`).
  - Fonts: Instrument Serif (display), Manrope (body), JetBrains Mono (labels/chips/meta).
  - Body grain SVG overlay (`.bg-grain`), animated gradient field (`.bg-field`), subtle grid (`.bg-grid`), vignette.
  - Holographic gradient borders on hover for all card variants via mask-composite trick.
  - Italic `<em>` inside headings renders as the holographic gradient.

- **WebGL hero shader** (`assets/app.js`)
  - Single fragment-shader plane attached to any `.hero-frame` / `[data-shader]` element.
  - FBM flow noise + chromatic offset + grain. Pointer-reactive (mouse warps the flow field).
  - Auto-pauses when offscreen via IntersectionObserver.
  - Graceful fallback to a static blurred gradient if WebGL is unavailable.
  - Replaces the old `tech-canvas` div soup (beams/discs/arcs) which is now hidden in CSS.

- **Motion engine** (`assets/app.js`)
  - Custom cursor (dot + lerped ring) with `mix-blend-mode: difference`. Disabled on coarse pointers.
  - Magnetic pull on `.button`, `button[type=submit]`, `.pill-link`, `.brand-mark`.
  - Split-text char reveal: headings get each character wrapped in `.split-char > span`, animated in on scroll.
  - Page-transition veil (clip-path wipe) on internal navigation. 580ms before navigation, 800ms wipe-out on arrival.
  - Reveal observer for `[data-reveal]` (kept original behavior, tuned timing).
  - Ticker seamless duplication so the marquee loops without a gap.

- **HTML edits** (all 4 pages)
  - Replaced hero-canvas decorations with a clean `<div class="hero-frame" data-shader>` + 4 corner `hero-tag-overlay` chips on `index.html`.
  - Sprinkled `<em>` around key phrases in every page hero/section heading to drive the holographic gradient (e.g. *more signal*, *one sharper*, *AI where useful*, *clear ask*).

### Bug fixed mid-session
`background-clip: text` on `<em>` stopped working once split-text wrapped chars in `display: inline-block` spans (each inline-block establishes its own clip context). Fix: re-applied the gradient directly to `em .split-char > span` in CSS.

### Verified in preview
- Hero shader renders the violet/pink/cyan flow on `index.html`.
- Holographic italics render correctly on all 4 page heroes.
- Page transitions wipe in/out between pages.
- Bottom-bar gradient CTA, custom cursor, and reveals all working.

### Commits this session
1. `Add Web3 holographic visual system` — full CSS rewrite.
2. `Add WebGL shader hero and motion` — full JS rewrite (shader + cursor + magnetics + split + transitions).
3. `Holographic headings and shader hero hook` — HTML edits across 4 pages.
4. `Fix gradient text inside split chars` — CSS fix for `<em>` clip-text after split.

### Not changed
- Any backend/ops/openclaw code.
- Any copy on the site.
- The 4-page structure or any class names the JS depends on.

## Next steps (if user wants more)
- Add a 3D mesh / R3F-style WebGL element if a single shader isn't enough.
- Scroll-linked horizontal pinning on the "Coverage" service rows.
- Replace the static page-hero areas with a smaller shader echo (currently only `index.html` has the hero shader; other pages keep the simpler header to load fast).
- Optional smooth-scroll (Lenis-style lerped scroll) if the user wants the buttery deep-scroll feel — costs ~5kb JS.
