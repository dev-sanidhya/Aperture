/* Aperture motion engine - magnetics, splits, transitions, reveals */

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const isCoarse = window.matchMedia("(hover: none), (pointer: coarse)").matches;

/* ---------------- Background scaffolding ---------------- */
(function injectBgLayers() {
  const layers = ["bg-field", "bg-grid", "bg-vignette"];
  layers.forEach((cls) => {
    if (!document.querySelector(`.${cls}`)) {
      const el = document.createElement("div");
      el.className = cls;
      document.body.prepend(el);
    }
  });

  if (!document.querySelector(".veil")) {
    const veil = document.createElement("div");
    veil.className = "veil";
    document.body.append(veil);
  }
})();

/* ---------------- Magnetic buttons ---------------- */
(function magnetics() {
  if (isCoarse || reduceMotion) return;
  const targets = document.querySelectorAll(".button, button[type='submit'], .brand-mark, .pill-link");
  targets.forEach((el) => {
    el.addEventListener("pointermove", (e) => {
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left - rect.width / 2) / rect.width;
      const y = (e.clientY - rect.top - rect.height / 2) / rect.height;
      el.style.transform = `translate3d(${x * 14}px, ${y * 10}px, 0)`;
    });
    el.addEventListener("pointerleave", () => {
      el.style.transform = "";
    });
  });
})();

/* ---------------- Reveal observer with staggered delays ---------------- */
(function reveals() {
  const els = document.querySelectorAll("[data-reveal]");
  if (!("IntersectionObserver" in window)) {
    els.forEach((e) => e.classList.add("revealed"));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          /* Stagger sibling cards inside grids */
          const parent = entry.target.parentElement;
          if (parent) {
            const siblings = parent.querySelectorAll("[data-reveal]");
            let idx = 0;
            siblings.forEach((sib) => {
              if (sib === entry.target) return;
              /* Check if this sibling is also intersecting or already revealed */
            });
          }
          entry.target.classList.add("revealed");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14, rootMargin: "0px 0px -8% 0px" }
  );

  /* Apply staggered delays to card grids */
  document.querySelectorAll(".services-grid, .work-grid, .contact-grid, .founders-stage, .timeline, .clients-grid, .clients-stats").forEach((grid) => {
    const cards = grid.querySelectorAll("[data-reveal]");
    cards.forEach((card, i) => {
      card.style.transitionDelay = `${i * 80}ms`;
    });
  });

  els.forEach((el) => io.observe(el));
})();

/* ---------------- Split text on headings ---------------- */
(function splitText() {
  const targets = document.querySelectorAll(".hero h1, .page-hero h1, .manifesto-title, .footer-form h2, .section-heading h2");
  targets.forEach((node) => {
    if (node.dataset.split === "true") return;
    node.dataset.split = "true";
    const html = node.innerHTML;
    const parser = new DOMParser();
    const doc = parser.parseFromString(`<div>${html}</div>`, "text/html");
    const root = doc.body.firstChild;

    function walk(el) {
      const out = document.createDocumentFragment();
      el.childNodes.forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const text = child.textContent || "";
          const words = text.split(/(\s+)/);
          words.forEach((word) => {
            if (!word) return;
            if (/^\s+$/.test(word)) {
              out.append(document.createTextNode(word));
              return;
            }
            const wordWrap = document.createElement("span");
            wordWrap.style.display = "inline-block";
            wordWrap.style.whiteSpace = "nowrap";
            [...word].forEach((ch, i) => {
              const box = document.createElement("span");
              box.className = "split-char";
              const inner = document.createElement("span");
              inner.textContent = ch;
              inner.style.setProperty("--d", `${i * 18}ms`);
              box.append(inner);
              wordWrap.append(box);
            });
            out.append(wordWrap);
          });
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          const clone = child.cloneNode(false);
          clone.appendChild(walk(child));
          out.append(clone);
        }
      });
      return out;
    }

    const newFrag = walk(root);
    node.innerHTML = "";
    node.append(newFrag);
  });

  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("split-ready");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.25 }
    );
    targets.forEach((el) => io.observe(el));
  } else {
    targets.forEach((el) => el.classList.add("split-ready"));
  }
})();

/* ---------------- Ticker seamless duplication ---------------- */
(function ticker() {
  document.querySelectorAll(".ticker-track").forEach((track) => {
    const html = track.innerHTML;
    track.innerHTML = html + html;
  });
})();

/* ---------------- Year + nav active ---------------- */
(function meta() {
  document.querySelectorAll("[data-year]").forEach((n) => { n.textContent = String(new Date().getFullYear()); });

  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  document.querySelectorAll("[data-nav]").forEach((link) => {
    const href = link.getAttribute("href");
    if (!href) return;
    if ((href === "/" && path === "/") || (href !== "/" && path.endsWith(href))) {
      link.classList.add("active");
    }
  });
})();

/* ---------------- Page transition wipe ---------------- */
(function pageTransitions() {
  const veil = document.querySelector(".veil");
  if (!veil) return;

  requestAnimationFrame(() => {
    veil.classList.add("veil-out");
    setTimeout(() => veil.classList.remove("veil-out"), 800);
  });

  document.addEventListener("click", (e) => {
    const target = e.target instanceof Element ? e.target.closest("a[href]") : null;
    if (!target) return;
    const href = target.getAttribute("href") || "";
    if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) return;
    if (target.target === "_blank") return;
    try {
      const url = new URL(href, window.location.href);
      if (url.origin !== window.location.origin) return;
      if (url.pathname === window.location.pathname) return;
    } catch { return; }

    e.preventDefault();
    veil.classList.add("veil-in");
    setTimeout(() => { window.location.href = href; }, 350);
  });
})();

/* ---------------- Mobile nav drawer ---------------- */
(function mobileNav() {
  const toggle = document.querySelector(".nav-toggle");
  if (!toggle) return;

  const overlay = document.createElement("div");
  overlay.className = "nav-overlay";

  const drawer = document.createElement("nav");
  drawer.className = "nav-drawer";

  document.querySelectorAll(".nav a[data-nav]").forEach((a) => {
    drawer.append(a.cloneNode(true));
  });

  document.body.append(overlay, drawer);

  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  drawer.querySelectorAll("a[data-nav]").forEach((link) => {
    const href = link.getAttribute("href");
    if (!href) return;
    if ((href === "/" && path === "/") || (href !== "/" && path.endsWith(href))) {
      link.classList.add("active");
    }
  });

  function open() {
    toggle.classList.add("is-open");
    drawer.classList.add("is-open");
    overlay.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function close() {
    toggle.classList.remove("is-open");
    drawer.classList.remove("is-open");
    overlay.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  toggle.addEventListener("click", () => {
    toggle.classList.contains("is-open") ? close() : open();
  });
  overlay.addEventListener("click", close);
  drawer.querySelectorAll("a").forEach((a) => a.addEventListener("click", close));
})();

/* ---------------- Intent chips + contact form ---------------- */
document.querySelectorAll("[data-intent-chip]").forEach((chip) => {
  chip.addEventListener("click", () => {
    const group = chip.closest("[data-intent-group]");
    const form = chip.closest("form");
    const briefField = form?.querySelector("textarea[name='brief']");
    if (!group || !(briefField instanceof HTMLTextAreaElement)) return;

    group.querySelectorAll("[data-intent-chip]").forEach((node) => node.classList.remove("is-selected"));
    chip.classList.add("is-selected");

    const value = chip.getAttribute("data-intent-chip");
    if (!value) return;
    if (!briefField.value.trim()) {
      briefField.value = `${value} project.`;
    } else if (!briefField.value.toLowerCase().includes(value.toLowerCase())) {
      briefField.value = `${value} project. ${briefField.value}`.trim();
    }
    briefField.focus();
  });
});

const FORM_ENDPOINT = "https://formsubmit.co/ajax/aperturecmservices@gmail.com";

document.querySelectorAll("[data-contact-form]").forEach((form) => {
  const statusNode = form.querySelector("[data-form-status]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!(form instanceof HTMLFormElement)) return;

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
      submitButton.textContent = "Sending…";
    }

    try {
      const response = await fetch(FORM_ENDPOINT, {
        method: "POST",
        headers: { Accept: "application/json" },
        body: payload,
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.message || "Unable to send inquiry.");
      form.reset();
      if (statusNode) {
        statusNode.textContent = "Inquiry sent. We'll reply within 48 hours.";
        statusNode.className = "form-status success";
      }
    } catch (error) {
      if (statusNode) {
        statusNode.textContent =
          error instanceof Error ? error.message : "Unable to send inquiry. Email us at aperturecmservice@gmail.com.";
        statusNode.className = "form-status error";
      }
    } finally {
      if (submitButton instanceof HTMLButtonElement) {
        submitButton.disabled = false;
        submitButton.textContent = "Send the brief";
      }
    }
  });
});
