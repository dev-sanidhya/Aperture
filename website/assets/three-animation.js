/* ═══════════════════════════════════════════════════════════
   Aperture — Global Three.js 3D Interactive Storytelling Logo
   Inspired by MetaMask's persistent, scrolling 3D elements
═══════════════════════════════════════════════════════════ */

(function() {
  const container = document.getElementById('global-3d-container');
  if (!container) return;

  // Set up Scene, Camera, Renderer
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.z = 10;

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);
  
  // Style container to be a fixed full-screen background
  container.style.position = 'fixed';
  container.style.top = '0';
  container.style.left = '0';
  container.style.width = '100vw';
  container.style.height = '100vh';
  container.style.zIndex = '-1';     // Sit behind all scrolling content
  container.style.pointerEvents = 'none';

  // ── 1. Create MetaMask-style low poly structure ──
  const globalGroup = new THREE.Group();
  scene.add(globalGroup);
  
  // Subgroup to handle local idle rotations vs scroll displacements
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
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
  scene.add(ambientLight);

  const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
  mainLight.position.set(5, 10, 7);
  scene.add(mainLight);

  const accentLight = new THREE.PointLight(0xd1a26a, 2.5, 50);
  accentLight.position.set(-5, 0, 5);
  scene.add(accentLight);

  // ── 3. Mouse Tracking (Cursor Look) ──
  let targetRotationX = 0;
  let targetRotationY = 0;
  let tmx = 0;
  let tmy = 0;
  
  document.addEventListener('mousemove', (e) => {
    tmx = (e.clientX / window.innerWidth) * 2 - 1;
    tmy = -(e.clientY / window.innerHeight) * 2 + 1;
    
    targetRotationY = tmx * (Math.PI * 0.35); 
    targetRotationX = tmy * (Math.PI * 0.35); 
  });

  // ── 4. Scroll Tracking (Storytelling displacement) ──
  window.addEventListener('load', () => {
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      // Storytelling Scroll sequence: smoothly pushes orb to the side as you scroll
      gsap.to(globalGroup.position, {
        x: 3.8, // Shift right into negative space
        y: 1.2, // Move slightly up
        z: -2.5, // Push slightly back
        ease: 'none',
        scrollTrigger: {
          trigger: document.body,
          start: 'top top',
          end: 'bottom bottom',
          scrub: 1.5, 
        }
      });
      
      gsap.to(globalGroup.rotation, {
        y: Math.PI * 1.5, 
        x: Math.PI * 0.3,
        ease: 'none',
        scrollTrigger: {
          trigger: document.body,
          start: 'top top',
          end: 'bottom bottom',
          scrub: 2,
        }
      });
    }
  });

  // ── 5. Animation Loop ──
  let idleTime = 0;
  
  const animate = function () {
    requestAnimationFrame(animate);
    idleTime += 0.005;

    // Smooth Lerp to target mouse rotation
    orbGroup.rotation.x += (targetRotationX - orbGroup.rotation.x) * 0.04;
    orbGroup.rotation.y += (targetRotationY - orbGroup.rotation.y) * 0.04;
    
    // Add base idle spin
    coreMesh.rotation.y += 0.006;
    coreMesh.rotation.x += 0.003;

    mesh.rotation.y -= 0.0015;
    wireframe.rotation.y -= 0.0015;
    
    // Gentle floating
    orbGroup.position.y = Math.sin(idleTime * 1.5) * 0.15;

    renderer.render(scene, camera);
  };

  // ── 6. Resize Handler ──
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // Start
  animate();
})();
