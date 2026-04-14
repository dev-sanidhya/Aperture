/* ═══════════════════════════════════════════════════════════
   Aperture — Inner Page Background: Subtle Particle Grid
   Replaces the 3D orb on services / process / contact pages
═══════════════════════════════════════════════════════════ */

(function () {
  const canvas = document.getElementById('inner-bg-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  // Style canvas as fixed full-screen background
  canvas.style.position = 'fixed';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100vw';
  canvas.style.height = '100vh';
  canvas.style.zIndex = '-1';
  canvas.style.pointerEvents = 'none';

  const GOLD  = { r: 209, g: 162, b: 106 };  // #d1a26a
  const TEAL  = { r: 143, g: 211, b: 196 };  // #8fd3c4

  let W, H, particles;
  const COUNT = 55;
  const LINK_DIST = 160;
  const LINK_DIST_SQ = LINK_DIST * LINK_DIST;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function randomColor() {
    return Math.random() > 0.5 ? GOLD : TEAL;
  }

  function makeParticle() {
    const c = randomColor();
    return {
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.28,
      vy: (Math.random() - 0.5) * 0.28,
      r: Math.random() * 1.4 + 0.6,
      c,
      // slow breathing opacity
      baseAlpha: Math.random() * 0.22 + 0.1,
      phase: Math.random() * Math.PI * 2,
      speed: Math.random() * 0.008 + 0.004,
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: COUNT }, makeParticle);
  }

  let t = 0;

  function draw() {
    ctx.clearRect(0, 0, W, H);
    t += 1;

    // Update + draw particles
    for (let i = 0; i < COUNT; i++) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;

      // Wrap edges
      if (p.x < -20) p.x = W + 20;
      else if (p.x > W + 20) p.x = -20;
      if (p.y < -20) p.y = H + 20;
      else if (p.y > H + 20) p.y = -20;

      // Breathing alpha
      const alpha = p.baseAlpha + Math.sin(t * p.speed + p.phase) * 0.07;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.c.r},${p.c.g},${p.c.b},${alpha.toFixed(3)})`;
      ctx.fill();
    }

    // Draw connecting lines between nearby particles
    for (let i = 0; i < COUNT; i++) {
      for (let j = i + 1; j < COUNT; j++) {
        const a = particles[i];
        const b = particles[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distSq = dx * dx + dy * dy;
        if (distSq < LINK_DIST_SQ) {
          const ratio = 1 - Math.sqrt(distSq) / LINK_DIST;
          // Blend colors toward whichever end is dominant
          const cr = Math.round((a.c.r + b.c.r) / 2);
          const cg = Math.round((a.c.g + b.c.g) / 2);
          const cb = Math.round((a.c.b + b.c.b) / 2);
          const lineAlpha = ratio * 0.12;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(${cr},${cg},${cb},${lineAlpha.toFixed(3)})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resize);
  init();
  draw();
})();
