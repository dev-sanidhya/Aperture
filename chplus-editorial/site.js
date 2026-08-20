document.querySelectorAll('[data-words]').forEach((el) => {
  const text = el.textContent;
  el.textContent = '';
  text.split(' ').forEach((w, i, arr) => {
    const span = document.createElement('span');
    span.textContent = w + (i < arr.length - 1 ? ' ' : '');
    el.appendChild(span);
  });
});

const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) {
      e.target.classList.add('is-in');
      io.unobserve(e.target);
    }
  });
}, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });

document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Cinematic reel: scroll-scrubbed pinned walkthrough (no autoplay — scroll drives playback)
const reelWrap = document.querySelector('.reel-wrap');
const reel = document.querySelector('.reel');
if (reelWrap && reel) {
  const videos = [...reel.querySelectorAll('video')];
  const dots = [...reel.querySelectorAll('.reel__rail span')];
  const captions = [...reel.querySelectorAll('.reel__caption [data-clip]')];
  const progressBar = reel.querySelector('.reel__progress');
  const durations = videos.map(() => 8);

  videos.forEach((v, i) => {
    v.muted = true; v.playsInline = true;
    v.addEventListener('loadedmetadata', () => { if (v.duration) durations[i] = v.duration; });
  });

  let activeIdx = -1;
  function setActive(idx) {
    if (idx === activeIdx) return;
    activeIdx = idx;
    videos.forEach((v, vi) => v.classList.toggle('is-active', vi === idx));
    dots.forEach((d, di) => d.classList.toggle('is-active', di === idx));
    captions.forEach((c, ci) => c.style.display = ci === idx ? '' : 'none');
  }

  function updateReel() {
    const rect = reelWrap.getBoundingClientRect();
    const total = reelWrap.offsetHeight - window.innerHeight;
    const progress = Math.min(1, Math.max(0, -rect.top / Math.max(1, total)));
    const segCount = videos.length;
    const segFloat = progress * segCount;
    const idx = Math.min(segCount - 1, Math.floor(segFloat));
    const local = Math.min(1, Math.max(0, segFloat - idx));
    setActive(idx);
    const v = videos[idx];
    if (v) {
      if (v.readyState === 0) v.load();
      if (v.readyState >= 1) v.currentTime = local * durations[idx];
    }
    if (progressBar) progressBar.style.width = (progress * 100) + '%';
  }

  window.addEventListener('scroll', updateReel, { passive: true });
  window.addEventListener('resize', updateReel);
  updateReel();
}

// Contents nav: cursor-following preview thumbnail
const contents = document.querySelector('.contents');
const preview = document.querySelector('.contents__preview');
if (contents && preview) {
  const previewImg = preview.querySelector('img');
  contents.querySelectorAll('.contents__row').forEach((row) => {
    row.addEventListener('mouseenter', () => {
      previewImg.src = row.dataset.preview;
      preview.classList.add('is-visible');
    });
    row.addEventListener('mouseleave', () => preview.classList.remove('is-visible'));
  });
  contents.addEventListener('mousemove', (e) => {
    preview.style.left = e.clientX + 28 + 'px';
    preview.style.top = e.clientY - 150 + 'px';
  });
}
