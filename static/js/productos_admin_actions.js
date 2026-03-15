// Acciones de la tabla de productos admin

document.addEventListener('DOMContentLoaded', function() {
  // Bloquear/desbloquear producto
  document.querySelectorAll('.products-table__button--block, .products-table__button--unblock').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const productId = this.dataset.productId;
      const action = this.dataset.action;
      fetch(`/administrador/productos/${productId}/${action}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Content-Type': 'application/json'
        }
      }).then(resp => {
        if (resp.ok) window.location.reload();
      });
    });
  });
});

function getCSRFToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}
