/* Aperture motion engine — WebGL hero, cursor, magnetics, splits, transitions */

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const isCoarse = window.matchMedia("(hover: none), (pointer: coarse)").matches;

/* ---------------- Background scaffolding ---------------- */
(function injectBgLayers() {
  const layers = ["bg-field", "bg-grid", "bg-vignette", "bg-grain"];
  layers.forEach((cls) => {
    if (!document.querySelector(`.${cls}`)) {
      const el = document.createElement("div");
      el.className = cls;
      document.body.prepend(el);
    }
  });

  if (!isCoarse && !document.querySelector(".cursor-ring")) {
    const ring = document.createElement("div");
    ring.className = "cursor-ring";
    const dot = document.createElement("div");
    dot.className = "cursor-dot";
    document.body.append(ring, dot);
  }

  if (!document.querySelector(".veil")) {
    const veil = document.createElement("div");
    veil.className = "veil";
    document.body.append(veil);
  }
})();

/* ---------------- Custom cursor ---------------- */
(function cursor() {
  if (isCoarse) return;
  const ring = document.querySelector(".cursor-ring");
  const dot = document.querySelector(".cursor-dot");
  if (!ring || !dot) return;

  let mx = window.innerWidth / 2;
  let my = window.innerHeight / 2;
  let rx = mx;
  let ry = my;

  window.addEventListener("pointermove", (e) => {
    mx = e.clientX;
    my = e.clientY;
    dot.style.transform = `translate3d(${mx}px, ${my}px, 0) translate(-50%, -50%)`;
  }, { passive: true });

  function frame() {
    rx += (mx - rx) * 0.18;
    ry += (my - ry) * 0.18;
    ring.style.transform = `translate3d(${rx}px, ${ry}px, 0) translate(-50%, -50%)`;
    requestAnimationFrame(frame);
  }
  frame();

  const hoverTargets = "a, button, .intent-chip, .pill-link, .contact-link, [data-magnetic]";
  document.addEventListener("pointerover", (e) => {
    if (e.target instanceof Element && e.target.closest(hoverTargets)) {
      document.body.classList.add("cursor-hover");
    }
  });
  document.addEventListener("pointerout", (e) => {
    if (e.target instanceof Element && e.target.closest(hoverTargets)) {
      document.body.classList.remove("cursor-hover");
    }
  });
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

/* ---------------- Reveal observer ---------------- */
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
          entry.target.classList.add("revealed");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14, rootMargin: "0px 0px -8% 0px" }
  );
  els.forEach((el) => io.observe(el));
})();

/* ---------------- Split text on headings ---------------- */
(function splitText() {
  const targets = document.querySelectorAll(".hero h1, .page-hero h1, .manifesto-title, .footer-form h2, .section-heading h2");
  targets.forEach((node) => {
    if (node.dataset.split === "true") return;
    node.dataset.split = "true";
    const html = node.innerHTML;
    // Wrap words to keep wrapping behavior; each word is a .split-char box; chars animate inside
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
              inner.style.setProperty("--d", `${i * 22}ms`);
              box.append(inner);
              wordWrap.append(box);
            });
            out.append(wordWrap);
          });
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          const clone = child.cloneNode(false);
          // recurse into children but keep wrapper (e.g., <em>)
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

/* ---------------- Scroll-driven scenes ---------------- */
(function scenes() {
  const sceneEls = document.querySelectorAll("[data-scene]");
  if (!sceneEls.length) return;

  const scenes = [...sceneEls].map((el) => {
    const beats = [...el.querySelectorAll("[data-beat]")].map((b) => {
      const [a, c] = (b.getAttribute("data-beat") || "0 1").split(/\s+/).map(Number);
      return { el: b, start: a, end: c };
    });
    return { el, beats };
  });

  function update() {
    const vh = window.innerHeight;
    for (const scene of scenes) {
      const rect = scene.el.getBoundingClientRect();
      const total = rect.height - vh;
      let p = 0;
      if (total > 0) {
        p = Math.min(1, Math.max(0, -rect.top / total));
      } else if (rect.top < vh && rect.bottom > 0) {
        p = 1 - rect.bottom / (rect.height + vh);
      }
      scene.el.style.setProperty("--p", p.toFixed(4));

      for (const beat of scene.beats) {
        const inRange = p >= beat.start && p <= beat.end;
        // local progress 0->1 within the beat range
        let local = 0;
        if (p < beat.start) local = 0;
        else if (p > beat.end) local = 1;
        else local = (p - beat.start) / Math.max(0.0001, beat.end - beat.start);
        beat.el.style.setProperty("--bp", local.toFixed(4));
        beat.el.classList.toggle("beat-active", inRange);
      }
    }
    rafPending = false;
  }

  let rafPending = false;
  function onScroll() {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(update);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  update();
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

  // Out animation on load
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
    setTimeout(() => { window.location.href = href; }, 580);
  });
})();

/* ---------------- WebGL hero shader ---------------- */
(function shader() {
  const frames = document.querySelectorAll(".hero-frame, [data-shader]");
  if (!frames.length) return;

  const VERT = `
    attribute vec2 a_pos;
    void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
  `;

  const FRAG = `
    precision highp float;
    uniform vec2 u_res;
    uniform float u_time;
    uniform vec2 u_mouse;

    // hash + simplex-ish noise
    vec2 hash2(vec2 p) {
      p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
      return -1.0 + 2.0 * fract(sin(p) * 43758.5453);
    }

    float noise(vec2 p) {
      const float K1 = 0.366025404;
      const float K2 = 0.211324865;
      vec2 i = floor(p + (p.x + p.y) * K1);
      vec2 a = p - i + (i.x + i.y) * K2;
      float m = step(a.y, a.x);
      vec2 o = vec2(m, 1.0 - m);
      vec2 b = a - o + K2;
      vec2 c = a - 1.0 + 2.0 * K2;
      vec3 h = max(0.5 - vec3(dot(a, a), dot(b, b), dot(c, c)), 0.0);
      vec3 n = h * h * h * h * vec3(
        dot(a, hash2(i + 0.0)),
        dot(b, hash2(i + o)),
        dot(c, hash2(i + 1.0))
      );
      return dot(n, vec3(70.0));
    }

    float fbm(vec2 p) {
      float v = 0.0;
      float a = 0.5;
      for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p *= 2.02;
        a *= 0.5;
      }
      return v;
    }

    void main() {
      vec2 uv = (gl_FragCoord.xy - 0.5 * u_res) / min(u_res.x, u_res.y);
      vec2 mouse = (u_mouse - 0.5);

      float t = u_time * 0.08;
      vec2 q = uv * 1.2;
      vec2 flow = vec2(
        fbm(q + vec2(t * 1.3, t * 0.7)),
        fbm(q + vec2(-t * 0.9, t * 1.1))
      );
      flow += mouse * 0.35;

      float f = fbm(q + flow * 1.6 + vec2(0.0, t * 0.6));
      float g = fbm(q * 1.6 + flow * 0.9 - vec2(t * 0.4, 0.0));
      float h = fbm(q * 0.7 - flow * 1.2 + vec2(t * 0.2, -t * 0.3));

      // cool iridescent palette (electric blue → cyan → violet)
      vec3 c1 = vec3(0.31, 0.49, 1.0);    // #4f7cff electric blue
      vec3 c2 = vec3(0.37, 0.91, 0.87);   // #5ee7df cyan
      vec3 c3 = vec3(0.55, 0.43, 1.0);    // #8b6dff violet
      vec3 c0 = vec3(0.018, 0.024, 0.05); // deep navy bg

      float m1 = smoothstep(-0.4, 0.6, f);
      float m2 = smoothstep(-0.3, 0.7, g);
      float m3 = smoothstep(-0.5, 0.5, h);

      vec3 col = c0;
      col = mix(col, c1, m1 * 0.55);
      col = mix(col, c2, m2 * 0.40);
      col = mix(col, c3, m3 * 0.35);

      // chromatic aberration tint
      float r = fbm(q * 1.05 + flow * 1.6 + vec2(0.02, t * 0.6));
      float b = fbm(q * 0.95 + flow * 1.6 + vec2(-0.02, t * 0.6));
      col.r += (r - f) * 0.18;
      col.b += (b - f) * 0.18;

      // soft vignette
      float vig = smoothstep(1.2, 0.2, length(uv));
      col *= 0.55 + 0.6 * vig;

      // grain
      float gn = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
      col += (gn - 0.5) * 0.035;

      gl_FragColor = vec4(col, 1.0);
    }
  `;

  function compile(gl, type, src) {
    const sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      console.warn("shader compile error", gl.getShaderInfoLog(sh));
      gl.deleteShader(sh);
      return null;
    }
    return sh;
  }

  frames.forEach((frame) => {
    // Insert canvas
    const canvas = document.createElement("canvas");
    canvas.className = "shader-canvas";
    frame.insertBefore(canvas, frame.firstChild);

    const gl = canvas.getContext("webgl", { antialias: false, premultipliedAlpha: false, alpha: false });
    if (!gl) {
      // Fallback: gradient
      canvas.style.background = "linear-gradient(135deg, #b794ff, #5ee7df, #ff79c6)";
      canvas.style.filter = "blur(40px) saturate(140%)";
      canvas.style.opacity = "0.55";
      return;
    }

    const vs = compile(gl, gl.VERTEX_SHADER, VERT);
    const fs = compile(gl, gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return;
    const prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.warn("program link error", gl.getProgramInfoLog(prog));
      return;
    }
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(prog, "a_pos");
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(prog, "u_res");
    const uTime = gl.getUniformLocation(prog, "u_time");
    const uMouse = gl.getUniformLocation(prog, "u_mouse");

    const dpr = Math.min(window.devicePixelRatio || 1, 1.6);
    let mx = 0.5, my = 0.5;
    let tx = 0.5, ty = 0.5;

    function resize() {
      const rect = frame.getBoundingClientRect();
      canvas.width = Math.max(2, Math.floor(rect.width * dpr));
      canvas.height = Math.max(2, Math.floor(rect.height * dpr));
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
    resize();
    new ResizeObserver(resize).observe(frame);

    frame.addEventListener("pointermove", (e) => {
      const r = frame.getBoundingClientRect();
      tx = (e.clientX - r.left) / r.width;
      ty = 1.0 - (e.clientY - r.top) / r.height;
    });

    const start = performance.now();
    let running = true;

    // pause when offscreen
    const io = new IntersectionObserver((entries) => {
      running = entries[0].isIntersecting;
      if (running) requestAnimationFrame(loop);
    }, { threshold: 0 });
    io.observe(frame);

    function loop() {
      if (!running) return;
      mx += (tx - mx) * 0.06;
      my += (ty - my) * 0.06;
      const t = reduceMotion ? 0 : (performance.now() - start) / 1000;
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, t);
      gl.uniform2f(uMouse, mx, my);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      requestAnimationFrame(loop);
    }
    loop();
  });
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

const FORM_ENDPOINT = "https://formsubmit.co/ajax/cachemoney0410@gmail.com";

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
      submitButton.textContent = "Sending";
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
