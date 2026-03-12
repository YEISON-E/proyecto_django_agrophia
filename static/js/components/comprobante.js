(function () {
  'use strict';

  /* ── Share button ──────────────────────────────────────────── */
  const shareBtn = document.getElementById('shareBtn');
  if (shareBtn) {
    shareBtn.addEventListener('click', async function () {
      const url   = window.location.href;
      const title = shareBtn.dataset.title || document.title;

      if (navigator.share) {
        try {
          await navigator.share({ title, url });
        } catch (_) { /* user cancelled */ }
      } else {
        try {
          await navigator.clipboard.writeText(url);
          showToast('Enlace copiado al portapapeles');
        } catch (_) {
          prompt('Copia este enlace:', url);
        }
      }
    });
  }

  /* ── Print button ──────────────────────────────────────────── */
  const printBtn = document.getElementById('printBtn');
  if (printBtn) {
    printBtn.addEventListener('click', function () {
      window.print();
    });
  }

  /* ── Toast helper ──────────────────────────────────────────── */
  function showToast(message) {
    const toast = document.getElementById('shareToast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
  }
})();
