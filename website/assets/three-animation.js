/* ═══════════════════════════════════════════════════════════
   Aperture — Global Three.js 3D Interactive Storytelling Logo
   Home page: full 3D orb with scroll storytelling
   Other pages: subtle particle network canvas
═══════════════════════════════════════════════════════════ */

(function() {
  const container = document.getElementById('global-3d-container');
  if (!container) return;

  // Style container to be a fixed full-screen background
  container.style.position = 'fixed';
  container.style.top = '0';
  container.style.left = '0';
  container.style.width = '100vw';
  container.style.height = '100vh';
  container.style.zIndex = '-1';
  container.style.pointerEvents = 'none';

  // Detect home page
  const path = window.location.pathname;
  const isHome = path === '/' || path.endsWith('/index.html') || path === '' || path.endsWith('/');

  if (isHome) {
    // ─────────────────────────────────────────────────────
    //  HOME PAGE — Full 3D Orb with scroll storytelling
    // ─────────────────────────────────────────────────────

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.z = 10;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // ── 1. Create MetaMask-style low poly structure ──
    const globalGroup = new THREE.Group();
    scene.add(globalGroup);

    const orbGroup = new THREE.Group();
    globalGroup.add(orbGroup);

    // Outer Tech Orb (Icosahedron)
    const geometry = new THREE.IcosahedronGeometry(3.2, 1);
    const material = new THREE.MeshPhysicalMaterial({
      color: 0xd1a26a,
      metalness: 0.1,
      roughness: 0.4,
      flatShading: true,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide
    });
    const mesh = new THREE.Mesh(geometry, material);
    orbGroup.add(mesh);

    // Inner Core
    const coreGeometry = new THREE.IcosahedronGeometry(1.6, 0);
    const coreMaterial = new THREE.MeshPhysicalMaterial({
      color: 0x8fd3c4,
      metalness: 0.8,
      roughness: 0.2,
      flatShading: true,
      transparent: true,
      opacity: 0.9
    });
    const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
    orbGroup.add(coreMesh);

    // Wireframe
    const wireMat = new THREE.LineBasicMaterial({ color: 0xd1a26a, transparent: true, opacity: 0.35 });
    const wireGeometry = new THREE.EdgesGeometry(geometry);
    const wireframe = new THREE.LineSegments(wireGeometry, wireMat);
    orbGroup.add(wireframe);

    // ── 2. Lighting ──
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
    mainLight.position.set(5, 10, 7);
    scene.add(mainLight);
    const accentLight = new THREE.PointLight(0xd1a26a, 2.5, 50);
    accentLight.position.set(-5, 0, 5);
    scene.add(accentLight);

    // ── 3. Mouse Tracking ──
    let targetRotationX = 0, targetRotationY = 0;
    document.addEventListener('mousemove', (e) => {
      const tmx = (e.clientX / window.innerWidth) * 2 - 1;
      const tmy = -(e.clientY / window.innerHeight) * 2 + 1;
      targetRotationY = tmx * (Math.PI * 0.35);
      targetRotationX = tmy * (Math.PI * 0.35);
    });

    // ── 4. Scroll Tracking ──
    window.addEventListener('load', () => {
      if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
        const isMobile = window.innerWidth <= 768;
        gsap.to(globalGroup.position, {
          x: isMobile ? 0.8 : 3.8,
          y: isMobile ? 0.6 : 1.2,
          z: isMobile ? -4 : -2.5,
          ease: 'none',
          scrollTrigger: { trigger: document.body, start: 'top top', end: 'bottom bottom', scrub: 1.5 }
        });
        gsap.to(globalGroup.rotation, {
          y: Math.PI * 1.5,
          x: Math.PI * 0.3,
          ease: 'none',
          scrollTrigger: { trigger: document.body, start: 'top top', end: 'bottom bottom', scrub: 2 }
        });
      }
    });

    // ── 5. Animation Loop ──
    let idleTime = 0;
    const animate = function () {
      requestAnimationFrame(animate);
      idleTime += 0.005;
      orbGroup.rotation.x += (targetRotationX - orbGroup.rotation.x) * 0.04;
      orbGroup.rotation.y += (targetRotationY - orbGroup.rotation.y) * 0.04;
      coreMesh.rotation.y += 0.006;
      coreMesh.rotation.x += 0.003;
      mesh.rotation.y -= 0.0015;
      wireframe.rotation.y -= 0.0015;
      orbGroup.position.y = Math.sin(idleTime * 1.5) * 0.15;
      renderer.render(scene, camera);
    };

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    animate();

  } else {
    // ─────────────────────────────────────────────────────
    //  INNER PAGES — Subtle particle network
    // ─────────────────────────────────────────────────────

    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');

    const GOLD = '209, 162, 106';
    const TEAL = '143, 211, 196';
    const COUNT = 72;
    const LINK_DIST = 160;
    const LINK_DIST_SQ = LINK_DIST * LINK_DIST;

    let W, H, particles;

    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }

    function randomParticle() {
      const isTeal = Math.random() < 0.35;
      return {
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.22,
        vy: (Math.random() - 0.5) * 0.22,
        r: 1.4 + Math.random() * 1.4,
        color: isTeal ? TEAL : GOLD,
        opacity: 0.25 + Math.random() * 0.35
      };
    }

    function init() {
      resize();
      particles = Array.from({ length: COUNT }, randomParticle);
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);

      // Draw connecting lines
      for (let i = 0; i < COUNT; i++) {
        for (let j = i + 1; j < COUNT; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const distSq = dx * dx + dy * dy;
          if (distSq < LINK_DIST_SQ) {
            const strength = 1 - distSq / LINK_DIST_SQ;
            const lineOpacity = strength * 0.18;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(${GOLD}, ${lineOpacity})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }

      // Draw dots
      for (const p of particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.color}, ${p.opacity})`;
        ctx.fill();
      }
    }

    function update() {
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        // Wrap edges
        if (p.x < -10) p.x = W + 10;
        if (p.x > W + 10) p.x = -10;
        if (p.y < -10) p.y = H + 10;
        if (p.y > H + 10) p.y = -10;
      }
    }

    function loop() {
      update();
      draw();
      requestAnimationFrame(loop);
    }

    window.addEventListener('resize', () => {
      resize();
      // Reposition particles within new bounds
      for (const p of particles) {
        p.x = Math.random() * W;
        p.y = Math.random() * H;
      }
    });

    init();
    loop();
  }
})();
