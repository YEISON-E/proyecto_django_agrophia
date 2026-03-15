document.addEventListener('DOMContentLoaded', function() {
  var modal = document.getElementById('adminMessageModal');
  if (modal) {
    modal.style.display = 'flex';
    var mensajeId = modal.dataset.mensajeId;
    function marcarLeido() {
      if (!mensajeId) return;
      fetch('/usuarios/marcar-mensaje-admin-leido/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'mensaje_id=' + encodeURIComponent(mensajeId)
      });
    }
    modal.querySelector('.modal-bg').onclick = function(e) {
      if (e.target === this) {
        modal.style.display = 'none';
        marcarLeido();
      }
    };
    modal.querySelector('.close-modal-btn').onclick = function() {
      modal.style.display = 'none';
      marcarLeido();
    };
  }
});

function getCSRFToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}
