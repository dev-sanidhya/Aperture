// ── Unified hero parallax (scroll + mouse, single RAF loop) ──
const heroSection = document.querySelector(".hero");
const orbA = document.querySelector(".orb-a");
const orbB = document.querySelector(".orb-b");
const orbC = document.querySelector(".orb-c");
const heroCopyEl = document.querySelector(".hero-copy");
const heroBullets = document.querySelector(".hero-bullets");
const heroActions = document.querySelector(".hero-actions");

// Mouse state (normalised -0.5 → +0.5)
let mx = 0, my = 0, tmx = 0, tmy = 0;
// Track latest scrollY for RAF
let latestScroll = window.scrollY;

if (heroSection) {
  heroSection.addEventListener("mousemove", (e) => {
    const rect = heroSection.getBoundingClientRect();
    tmx = (e.clientX - rect.left) / rect.width - 0.5;
    tmy = (e.clientY - rect.top) / rect.height - 0.5;
  });
  heroSection.addEventListener("mouseleave", () => { tmx = 0; tmy = 0; });
}

window.addEventListener("scroll", () => { latestScroll = window.scrollY; }, { passive: true });

const tickParallax = () => {
  mx += (tmx - mx) * 0.06;
  my += (tmy - my) * 0.06;
  const sy = latestScroll;

  if (orbA) orbA.style.transform = `translate(${sy * 0.08 + mx * -32}px, ${sy * 0.14 + my * -24}px)`;
  if (orbB) orbB.style.transform = `translate(${sy * -0.06 + mx * 26}px, ${sy * 0.10 + my * -20}px)`;
  if (orbC) orbC.style.transform = `translate(${sy * 0.04 + mx * -16}px, ${sy * -0.08 + my * 22}px)`;
  // Orbs only — hero copy no longer parallaxes (was pushing content into ticker)
  if (heroBullets) heroBullets.style.transform = `translate(${mx * 9}px, ${my * 7}px)`;
  if (heroActions) heroActions.style.transform = `translate(${mx * 6}px, ${my * 5}px)`;

  requestAnimationFrame(tickParallax);
};
tickParallax();

// ── Cursor glow ─────────────────────────────────────────────
const cursorGlow = document.querySelector(".cursor-glow");
if (cursorGlow && window.matchMedia("(pointer: fine)").matches) {
  let cx = -9999, cy = -9999;
  let tx = -9999, ty = -9999;
  let rafId;

  document.addEventListener("mousemove", (e) => {
    tx = e.clientX;
    ty = e.clientY;
  });

  document.addEventListener("mouseleave", () => {
    tx = -9999;
    ty = -9999;
  });

  const lerp = (a, b, t) => a + (b - a) * t;

  const tickGlow = () => {
    cx = lerp(cx, tx, 0.07);
    cy = lerp(cy, ty, 0.07);
    cursorGlow.style.transform = `translate(${cx - 350}px, ${cy - 350}px)`;
    rafId = requestAnimationFrame(tickGlow);
  };
  tickGlow();
}

// ── Hero h1 word-reveal ─────────────────────────────────────
const heroH1 = document.querySelector(".hero h1");
if (heroH1) {
  const words = heroH1.textContent.trim().split(/\s+/);
  heroH1.innerHTML = words
    .map(
      (w, i) =>
        `<span class="word-wrap"><span class="word" style="animation-delay:${i * 85}ms">${w}</span></span>`
    )
    .join(" ");
}

// ── Magnetic primary buttons ────────────────────────────────
document.querySelectorAll(".button-primary").forEach((btn) => {
  btn.addEventListener("mousemove", (e) => {
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    btn.style.transform = `translate(${x * 0.18}px, ${y * 0.28}px) translateY(-1px)`;
  });
  btn.addEventListener("mouseleave", () => {
    btn.style.transform = "";
  });
});

// ── Scroll reveal ────────────────────────────────────────────
const revealElements = document.querySelectorAll("[data-reveal]");

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("revealed");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

revealElements.forEach((element) => observer.observe(element));

// ── Orbit bento — scroll-scrub engine ────────────────────────
// Each card has a start position (off-screen) + rotation.
// As you scroll the section into view, progress 0→1 drives
// every card smoothly to its final resting place — just like
// MetaMask's scroll-driven bento grid.
(function () {
  const section  = document.querySelector(".orbit-section");
  const cards    = [...document.querySelectorAll("[data-orbit-card]")];
  const center   = document.querySelector("[data-orbit-center]");
  if (!section || !cards.length) return;

  // Starting offsets + rotation for each card (tl, tr, bl, br)
  const CONFIGS = [
    { x: -200, y: -140, r: -14 },
    { x:  200, y: -140, r:  14 },
    { x: -200, y:  140, r:  14 },
    { x:  200, y:  140, r: -14 },
  ];

  // Stagger: each card starts animating a little later than previous
  const STAGGER = 0.07;

  function easeOutQuart(t) {
    return 1 - Math.pow(1 - t, 4);
  }

  function getProgress() {
    const rect = section.getBoundingClientRect();
    const vh   = window.innerHeight;
    // 0 = section bottom just enters viewport
    // 1 = section top is at 25% of viewport height
    const raw = (vh - rect.top) / (vh * 0.75 + rect.height * 0.5);
    return Math.max(0, Math.min(1, raw));
  }

  function tick() {
    const progress = getProgress();

    // Center mark — pops in first
    if (center) {
      const cp = easeOutQuart(Math.min(1, progress * 2));
      center.style.opacity   = cp;
      center.style.transform = `scale(${0.55 + cp * 0.45})`;
    }

    // Cards — each one chases progress with its own stagger delay
    cards.forEach((card, i) => {
      const cfg = CONFIGS[i] || CONFIGS[0];
      const delay = i * STAGGER;
      const p = Math.max(0, Math.min(1, (progress - delay) / (1 - delay * cards.length * 0.5 + 0.001)));
      const e = easeOutQuart(p);

      card.style.opacity   = Math.min(1, e * 1.6);
      card.style.transform = `translate(${cfg.x * (1 - e)}px, ${cfg.y * (1 - e)}px) rotate(${cfg.r * (1 - e)}deg)`;
    });
  }

  // RAF-throttled scroll listener
  let rafPending = false;
  window.addEventListener("scroll", () => {
    if (!rafPending) {
      rafPending = true;
      requestAnimationFrame(() => { tick(); rafPending = false; });
    }
  }, { passive: true });

  // Run once immediately in case section is already in view
  tick();
})();

// ── Manifesto list line-by-line reveal ───────────────────────
const manifestoList = document.querySelector(".manifesto-list");
if (manifestoList) {
  const manifestoObs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("revealed");
          manifestoObs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );
  manifestoObs.observe(manifestoList);
}

// ── Service row index count-up ───────────────────────────────
document.querySelectorAll(".service-row-index").forEach((el, i) => {
  const target = i + 1;
  const countObs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        countObs.unobserve(entry.target);
        let start = 0;
        const duration = 900;
        const startTime = performance.now();
        const tick = (now) => {
          const p = Math.min((now - startTime) / duration, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          const val = Math.round(eased * target);
          entry.target.textContent = String(val).padStart(2, "0");
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    },
    { threshold: 0.5 }
  );
  countObs.observe(el);
});

const yearNode = document.querySelector("[data-year]");
if (yearNode) {
  yearNode.textContent = String(new Date().getFullYear());
}

const path = window.location.pathname.replace(/\/+$/, "") || "/";
document.querySelectorAll("[data-nav]").forEach((link) => {
  const href = link.getAttribute("href");
  if (!href) {
    return;
  }

  if ((href === "/" && path === "/") || (href !== "/" && path.endsWith(href))) {
    link.classList.add("active");
  }
});

const menuToggle = document.querySelector("[data-menu-toggle]");
const mobileNav = document.querySelector("[data-mobile-nav]");

if (menuToggle instanceof HTMLButtonElement && mobileNav instanceof HTMLElement) {
  const closeMenu = () => {
    menuToggle.classList.remove("is-open");
    mobileNav.classList.remove("is-open");
    menuToggle.setAttribute("aria-expanded", "false");
    document.body.classList.remove("menu-open");
  };

  const openMenu = () => {
    menuToggle.classList.add("is-open");
    mobileNav.classList.add("is-open");
    menuToggle.setAttribute("aria-expanded", "true");
    document.body.classList.add("menu-open");
  };

  menuToggle.addEventListener("click", () => {
    if (mobileNav.classList.contains("is-open")) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  mobileNav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMenu);
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 640) {
      closeMenu();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMenu();
    }
  });

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Node)) {
      return;
    }
    if (!mobileNav.contains(event.target) && !menuToggle.contains(event.target)) {
      closeMenu();
    }
  });
}

document.querySelectorAll("[data-tilt-scene]").forEach((scene) => {
  const resetScene = () => {
    scene.style.setProperty("--scene-rotate-x", "-12deg");
    scene.style.setProperty("--scene-rotate-y", "14deg");
    scene.style.setProperty("--scene-shift-x", "0px");
    scene.style.setProperty("--scene-shift-y", "0px");
  };

  resetScene();

  scene.addEventListener("pointermove", (event) => {
    const rect = scene.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    scene.style.setProperty("--scene-rotate-x", `${-12 - y * 18}deg`);
    scene.style.setProperty("--scene-rotate-y", `${14 + x * 22}deg`);
    scene.style.setProperty("--scene-shift-x", `${x * 28}px`);
    scene.style.setProperty("--scene-shift-y", `${y * 28}px`);
  });

  scene.addEventListener("pointerleave", resetScene);
});

document.querySelectorAll("[data-intent-chip]").forEach((chip) => {
  chip.addEventListener("click", () => {
    const group = chip.closest("[data-intent-group]");
    const form = chip.closest("form");
    const briefField = form?.querySelector("textarea[name='brief']");
    if (!group || !(briefField instanceof HTMLTextAreaElement)) {
      return;
    }

    group.querySelectorAll("[data-intent-chip]").forEach((node) => node.classList.remove("is-selected"));
    chip.classList.add("is-selected");

    const value = chip.getAttribute("data-intent-chip");
    if (!value) {
      return;
    }

    if (!briefField.value.trim()) {
      briefField.value = `${value} project.`;
    } else if (!briefField.value.toLowerCase().includes(value.toLowerCase())) {
      briefField.value = `${value} project. ${briefField.value}`.trim();
    }

    briefField.focus();
  });
});

const FORM_ENDPOINT = "https://formsubmit.co/ajax/cachemoney0410@gmail.com";

document.querySelectorAll("[data-contact-form]").forEach((form) => {
  const statusNode = form.querySelector("[data-form-status]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!(form instanceof HTMLFormElement)) {
      return;
    }

    const submitButton = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const company = String(formData.get("company") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const brief = String(formData.get("brief") || "").trim();
    const payload = new FormData();
    payload.append("company", company);
    payload.append("email", email);
    payload.append("brief", brief);
    payload.append("_subject", `New Aperture inquiry from ${company}`);
    payload.append("_captcha", "false");
    payload.append("_template", "table");

    if (statusNode) {
      statusNode.textContent = "Sending inquiry...";
      statusNode.className = "form-status";
    }

    if (submitButton instanceof HTMLButtonElement) {
      submitButton.disabled = true;
      submitButton.textContent = "Sending";
    }

    try {
      const response = await fetch(FORM_ENDPOINT, {
        method: "POST",
        headers: { Accept: "application/json" },
        body: payload,
      });

      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.message || "Unable to send inquiry.");
      }

      form.reset();
      if (statusNode) {
        statusNode.textContent = "Inquiry sent. Aperture will reach out shortly.";
        statusNode.className = "form-status success";
      }
    } catch (error) {
      if (statusNode) {
        statusNode.textContent =
          error instanceof Error ? error.message : "Unable to send inquiry. Email us at cachemoney0410@gmail.com.";
        statusNode.className = "form-status error";
      }
    } finally {
      if (submitButton instanceof HTMLButtonElement) {
        submitButton.disabled = false;
        submitButton.textContent = "Start the conversation";
      }
    }
  });
});
