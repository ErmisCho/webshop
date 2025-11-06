// --- Simple Lightbox Preview ---
document.addEventListener("DOMContentLoaded", () => {
  const gallery = Array.from(document.querySelectorAll('[data-gallery-item] img'));
  if (!gallery.length) return;
  const root = document.getElementById("lux-lightbox-root");
  if (!root) return;

  const lb = document.createElement('div');
  lb.id = 'lightbox';
  lb.className = 'fixed inset-0 z-50 hidden';
  lb.innerHTML = `
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>
    <button id="lbClose" class="absolute top-4 right-4 text-white/80 hover:text-white" aria-label="Close">
      <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
    <div class="absolute inset-0 flex items-center justify-center p-4">
      <button id="lbPrev" class="text-white/80 hover:text-white p-2" aria-label="Previous">
        <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
      <img id="lbImg" src="" alt="Preview" class="max-h-[85vh] max-w-[92vw] object-contain shadow-2xl" />
      <button id="lbNext" class="text-white/80 hover:text-white p-2" aria-label="Next">
        <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>
  `;
  document.body.appendChild(lb);

  const lbImg = lb.querySelector('#lbImg');
  const lbClose = lb.querySelector('#lbClose');
  const lbPrev = lb.querySelector('#lbPrev');
  const lbNext = lb.querySelector('#lbNext');
  let idx = 0;

  function openLB(i) { idx = i; lbImg.src = gallery[idx].src; lb.classList.remove('hidden'); document.body.style.overflow = 'hidden'; }
  function closeLB() { lb.classList.add('hidden'); document.body.style.overflow = ''; }
  function prev() { idx = (idx - 1 + gallery.length) % gallery.length; lbImg.src = gallery[idx].src; }
  function next() { idx = (idx + 1) % gallery.length; lbImg.src = gallery[idx].src; }

  gallery.forEach((img, i) => img.parentElement.addEventListener('click', e => { e.preventDefault(); openLB(i); }));
  lbClose.addEventListener('click', closeLB);
  lb.addEventListener('click', e => { if (e.target === lb) closeLB(); });
  lbPrev.addEventListener('click', prev);
  lbNext.addEventListener('click', next);
  document.addEventListener('keydown', e => {
    if (lb.classList.contains('hidden')) return;
    if (e.key === 'Escape') closeLB();
    if (e.key === 'ArrowLeft') prev();
    if (e.key === 'ArrowRight') next();
  });
});
