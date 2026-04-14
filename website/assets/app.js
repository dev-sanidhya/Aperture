/* ═══════════════════════════════════════════════════════════
   Aperture — Animation System
   GSAP 3 + ScrollTrigger + Lenis smooth scroll
   Inspired by MetaMask's premium animation architecture
═══════════════════════════════════════════════════════════ */

gsap.registerPlugin(ScrollTrigger);

// ── 1. Lenis smooth scroll (studio-freight pattern) ──────────
const lenis = new Lenis({
  lerp: 0.1,
  smoothWheel: true,
  orientation: 'vertical',
});

// Keep GSAP ScrollTrigger in sync with Lenis virtualised scroll
lenis.on('scroll', ScrollTrigger.update);

// Drive Lenis via GSAP's global ticker — same pattern as MetaMask
gsap.ticker.add((time) => {
  lenis.raf(time * 1000);
});
gsap.ticker.lagSmoothing(0);

// Remove native smooth scroll — Lenis handles it
document.documentElement.style.scrollBehavior = 'auto';

// ── 2. Cursor glow — GSAP ticker lerp (no separate RAF) ──────
const cursorGlow = document.querySelector('.cursor-glow');
if (cursorGlow && window.matchMedia('(pointer: fine)').matches) {
  let cx = -9999, cy = -9999, tx = -9999, ty = -9999;

  document.addEventListener('mousemove', (e) => { tx = e.clientX; ty = e.clientY; });
  document.addEventListener('mouseleave', () => { tx = -9999; ty = -9999; });

  gsap.ticker.add(() => {
    cx += (tx - cx) * 0.07;
    cy += (ty - cy) * 0.07;
    gsap.set(cursorGlow, { x: cx - 350, y: cy - 350 });
  });
}

// ── 3. Hero word-split ────────────────────────────────────────
const heroH1 = document.querySelector('.hero h1');
if (heroH1) {
  const words = heroH1.textContent.trim().split(/\s+/);
  heroH1.innerHTML = words
    .map((w, i) => `<span class="word-wrap"><span class="word" style="animation-delay:${i * 85}ms">${w}</span></span>`)
    .join(' ');
}

// ── 4. Hero entrance — GSAP timeline (MetaMask expo.out feel) ─
const heroTl = gsap.timeline({ defaults: { ease: 'expo.out', duration: 1.1 } });

const eyebrow   = document.querySelector('.js-hero-eyebrow');
const heroLead  = document.querySelector('.js-hero-lead');
const heroActs  = document.querySelector('.js-hero-actions');
const heroBulls = document.querySelector('.js-hero-bullets');
const heroShowcase = document.querySelector('.js-hero-showcase');
const heroVisual   = document.querySelector('.hero-visual-desktop');

if (eyebrow)      heroTl.from(eyebrow,      { autoAlpha: 0, x: -20 }, 0.35);
if (heroLead)     heroTl.from(heroLead,     { autoAlpha: 0, y: 20  }, 0.55);
if (heroActs)     heroTl.from(heroActs,     { autoAlpha: 0, y: 20  }, 0.7);
if (heroBulls)    heroTl.from(heroBulls,    { autoAlpha: 0, y: 16  }, 0.85);
if (heroShowcase) heroTl.from(heroShowcase, { autoAlpha: 0, y: 30  }, 0.5);
if (heroVisual)   heroTl.from(heroVisual,   { autoAlpha: 0, y: 30  }, 0.6);

// ── 5. Hero parallax — GSAP ticker (combined scroll + mouse) ──
const heroSection = document.querySelector('.hero');
const orbA = document.querySelector('.orb-a');
const orbB = document.querySelector('.orb-b');
const orbC = document.querySelector('.orb-c');

let mx = 0, my = 0, tmx = 0, tmy = 0;

if (heroSection) {
  heroSection.addEventListener('mousemove', (e) => {
    const r = heroSection.getBoundingClientRect();
    tmx = (e.clientX - r.left) / r.width  - 0.5;
    tmy = (e.clientY - r.top)  / r.height - 0.5;
  });
  heroSection.addEventListener('mouseleave', () => { tmx = 0; tmy = 0; });
}

gsap.ticker.add(() => {
  mx += (tmx - mx) * 0.06;
  my += (tmy - my) * 0.06;
  const sy = lenis.scroll || window.scrollY;

  if (orbA) gsap.set(orbA, { x: sy * 0.08  + mx * -32, y: sy * 0.14  + my * -24 });
  if (orbB) gsap.set(orbB, { x: sy * -0.06 + mx *  26, y: sy * 0.10  + my * -20 });
  if (orbC) gsap.set(orbC, { x: sy * 0.04  + mx * -16, y: sy * -0.08 + my *  22 });
  if (heroActs)  gsap.set(heroActs,  { x: mx * 6, y: my * 5 });
  if (heroBulls) gsap.set(heroBulls, { x: mx * 9, y: my * 7 });
});

// ── 6. Magnetic buttons — GSAP ticker lerp (MetaMask Magnetic class) ──
class MagneticBtn {
  constructor(el) {
    this.el = el;
    this.tx = 0; this.ty = 0;
    this.cx = 0; this.cy = 0;

    el.addEventListener('mousemove', (e) => {
      const r = el.getBoundingClientRect();
      this.tx = (e.clientX - r.left - r.width  / 2) * 0.38;
      this.ty = (e.clientY - r.top  - r.height / 2) * 0.38;
    });
    el.addEventListener('mouseleave', () => { this.tx = 0; this.ty = 0; });

    gsap.ticker.add(() => {
      this.cx += (this.tx - this.cx) * 0.1;
      this.cy += (this.ty - this.cy) * 0.1;
      gsap.set(el, { x: this.cx, y: this.cy });
    });
  }
}
document.querySelectorAll('.button-primary, .button-secondary').forEach((btn) => new MagneticBtn(btn));

// ── 7. Scroll reveals — GSAP ScrollTrigger (replaces IntersectionObserver) ──
gsap.utils.toArray('[data-reveal]').forEach((el) => {
  gsap.fromTo(el,
    { autoAlpha: 0, y: 44, filter: 'blur(6px)', scale: 0.97 },
    {
      autoAlpha: 1, y: 0, filter: 'blur(0px)', scale: 1,
      duration: 1,
      ease: 'expo.out',
      scrollTrigger: {
        trigger: el,
        start: 'top 88%',
        once: true,
      },
    }
  );
});

// ── 8. Orbit section — GSAP ScrollTrigger scrub (MetaMask bento style) ──
(() => {
  const section = document.querySelector('.orbit-section');
  const cards   = gsap.utils.toArray('[data-orbit-card]');
  const center  = document.querySelector('[data-orbit-center]');
  if (!section || !cards.length) return;

  const isMobile = window.innerWidth <= 640;
  
  const CONFIGS = isMobile 
    ? [
        { x: -50, y: -50, rotation: -10 },
        { x:  50, y: -50, rotation:  10 },
        { x: -50, y:  50, rotation:  10 },
        { x:  50, y:  50, rotation: -10 },
      ]
    : [
        { x: -200, y: -150, rotation: -14 }, // TL
        { x:  200, y: -150, rotation:  14 }, // TR
        { x: -200, y:  150, rotation:  14 }, // BL
        { x:  200, y:  150, rotation: -14 }, // BR
      ];

  // Set hidden starting state
  gsap.set(cards, { autoAlpha: 0 });
  cards.forEach((card, i) => {
    const cfg = CONFIGS[i] || CONFIGS[0];
    gsap.set(card, { x: cfg.x, y: cfg.y, rotation: cfg.rotation });
  });
  if (center) gsap.set(center, { autoAlpha: 0, scale: 0.55 });

  // Build scroll-scrubbed timeline — exactly like MetaMask's bento
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: section,
      start: 'top 75%',
      end:   'top 15%',
      scrub: 0.9,
    },
  });

  // Center iris pops in first
  if (center) {
    tl.to(center, { autoAlpha: 1, scale: 1, ease: 'power4.out', duration: 0.35 }, 0);
  }

  // Cards fly in with staggered scrub
  cards.forEach((card, i) => {
    const cfg = CONFIGS[i] || CONFIGS[0];
    tl.to(card, {
      autoAlpha: 1,
      x: 0, y: 0,
      rotation: 0,
      ease: 'power4.out',
      duration: 0.5,
    }, i * 0.08);
  });
})();

// ── 9. Manifesto stagger — GSAP ScrollTrigger ────────────────
const manifestoList = document.querySelector('.manifesto-list');
if (manifestoList) {
  gsap.fromTo(
    [...manifestoList.children],
    { autoAlpha: 0, x: -28 },
    {
      autoAlpha: 1, x: 0,
      stagger: 0.13,
      ease: 'expo.out',
      duration: 1,
      scrollTrigger: {
        trigger: manifestoList,
        start: 'top 80%',
        once: true,
      },
    }
  );
}

// ── 10. Brand-mark idle rotation (GSAP ticker — subtle) ───────
const brandBlades = document.querySelector('.brand-blades');
if (brandBlades) {
  let angle = 0;
  gsap.ticker.add(() => {
    angle += 0.012; // ~0.7 rpm
    gsap.set(brandBlades, { rotation: angle, transformOrigin: '18px 18px', svgOrigin: '18 18' });
  });
}

// ── 11. Tilt canvas (Removed in favor of WebGL 3D) ──────────────

// ── 12. Functional: year, nav active, mobile menu ────────────
const yearNode = document.querySelector('[data-year]');
if (yearNode) yearNode.textContent = String(new Date().getFullYear());

const path = window.location.pathname.replace(/\/+$/, '') || '/';
document.querySelectorAll('[data-nav]').forEach((link) => {
  const href = link.getAttribute('href');
  if (!href) return;
  if ((href === '/' && path === '/') || (href !== '/' && path.endsWith(href))) {
    link.classList.add('active');
  }
});

const menuToggle = document.querySelector('[data-menu-toggle]');
const mobileNav  = document.querySelector('[data-mobile-nav]');
if (menuToggle instanceof HTMLButtonElement && mobileNav instanceof HTMLElement) {
  const closeMenu = () => {
    menuToggle.classList.remove('is-open');
    mobileNav.classList.remove('is-open');
    menuToggle.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('menu-open');
  };
  const openMenu = () => {
    menuToggle.classList.add('is-open');
    mobileNav.classList.add('is-open');
    menuToggle.setAttribute('aria-expanded', 'true');
    document.body.classList.add('menu-open');
  };
  menuToggle.addEventListener('click', () =>
    mobileNav.classList.contains('is-open') ? closeMenu() : openMenu()
  );
  mobileNav.querySelectorAll('a').forEach((l) => l.addEventListener('click', closeMenu));
  window.addEventListener('resize', () => { if (window.innerWidth > 640) closeMenu(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(); });
  document.addEventListener('click', (e) => {
    if (!(e.target instanceof Node)) return;
    if (!mobileNav.contains(e.target) && !menuToggle.contains(e.target)) closeMenu();
  });
}

// ── 13. Intent chips ──────────────────────────────────────────
document.querySelectorAll('[data-intent-chip]').forEach((chip) => {
  chip.addEventListener('click', () => {
    const group      = chip.closest('[data-intent-group]');
    const form       = chip.closest('form');
    const briefField = form?.querySelector("textarea[name='brief']");
    if (!group || !(briefField instanceof HTMLTextAreaElement)) return;
    group.querySelectorAll('[data-intent-chip]').forEach((n) => n.classList.remove('is-selected'));
    chip.classList.add('is-selected');
    const value = chip.getAttribute('data-intent-chip');
    if (!value) return;
    if (!briefField.value.trim()) {
      briefField.value = `${value} project.`;
    } else if (!briefField.value.toLowerCase().includes(value.toLowerCase())) {
      briefField.value = `${value} project. ${briefField.value}`.trim();
    }
    briefField.focus();
  });
});

// ── 14. Contact form ──────────────────────────────────────────
const FORM_ENDPOINT = 'https://formsubmit.co/ajax/cachemoney0410@gmail.com';
document.querySelectorAll('[data-contact-form]').forEach((form) => {
  const statusNode = form.querySelector('[data-form-status]');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!(form instanceof HTMLFormElement)) return;
    const btn     = form.querySelector("button[type='submit']");
    const fd      = new FormData(form);
    const payload = new FormData();
    payload.append('company',  String(fd.get('company') || '').trim());
    payload.append('email',    String(fd.get('email')   || '').trim());
    payload.append('brief',    String(fd.get('brief')   || '').trim());
    payload.append('_subject', `New Aperture inquiry from ${String(fd.get('company') || '').trim()}`);
    payload.append('_captcha', 'false');
    payload.append('_template', 'table');
    if (statusNode) { statusNode.textContent = 'Sending inquiry...'; statusNode.className = 'form-status'; }
    if (btn instanceof HTMLButtonElement) { btn.disabled = true; btn.textContent = 'Sending'; }
    try {
      const res    = await fetch(FORM_ENDPOINT, { method: 'POST', headers: { Accept: 'application/json' }, body: payload });
      const result = await res.json();
      if (!res.ok) throw new Error(result.message || 'Unable to send inquiry.');
      form.reset();
      if (statusNode) { statusNode.textContent = 'Inquiry sent. Aperture will reach out shortly.'; statusNode.className = 'form-status success'; }
    } catch (err) {
      if (statusNode) { statusNode.textContent = err instanceof Error ? err.message : 'Unable to send. Email cachemoney0410@gmail.com.'; statusNode.className = 'form-status error'; }
    } finally {
      if (btn instanceof HTMLButtonElement) { btn.disabled = false; btn.textContent = 'Start the conversation'; }
    }
  });
});
