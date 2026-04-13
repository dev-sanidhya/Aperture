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
  { threshold: 0.16 }
);

revealElements.forEach((element) => observer.observe(element));

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
