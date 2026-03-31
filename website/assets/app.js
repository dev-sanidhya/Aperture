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
