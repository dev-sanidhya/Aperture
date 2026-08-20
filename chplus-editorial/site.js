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
