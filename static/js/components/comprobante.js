(function () {
  'use strict';

  /* ── Local date/time (user computer timezone) ─────────────── */
  const localDateNodes = document.querySelectorAll('.receipt-local-datetime[data-iso]');
  if (localDateNodes.length) {
    localDateNodes.forEach((node) => {
      const iso = node.dataset.iso;
      const format = node.dataset.format || 'short';
      const date = new Date(iso);
      if (Number.isNaN(date.getTime())) {
        return;
      }

      const options = format === 'long'
        ? {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
            hourCycle: 'h12',
          }
        : {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
            hourCycle: 'h12',
          };

      const formatted = new Intl.DateTimeFormat('es-CO', options).format(date);
      node.textContent = formatted;
    });
  }

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
