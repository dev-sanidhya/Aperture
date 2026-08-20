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

// Cinematic reel: crossfade between looping ambient clips
const reel = document.querySelector('.reel');
if (reel) {
  const videos = [...reel.querySelectorAll('video')];
  const dots = [...reel.querySelectorAll('.reel__dots span')];
  const captions = [...reel.querySelectorAll('.reel__caption [data-clip]')];
  let active = 0;

  function activate(i) {
    videos.forEach((v, vi) => v.classList.toggle('is-active', vi === i));
    dots.forEach((d, di) => d.classList.toggle('is-active', di === i));
    captions.forEach((c, ci) => c.style.display = ci === i ? '' : 'none');
    const v = videos[i];
    if (v) { v.currentTime = 0; v.play().catch(() => {}); }
  }

  videos.forEach((v, i) => {
    v.muted = true; v.playsInline = true;
    v.addEventListener('ended', () => activate((i + 1) % videos.length));
  });

  activate(0);
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
