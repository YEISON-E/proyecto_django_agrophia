// Archivo de acciones para la tabla de productos en el panel admin.

// Espera a que el DOM esté listo antes de enlazar eventos.
document.addEventListener('DOMContentLoaded', function() {
  // Busca botones de bloquear y desbloquear producto.
  document.querySelectorAll('.products-table__button--block, .products-table__button--unblock').forEach(function(btn) {
    // Asocia clic a cada botón encontrado.
    btn.addEventListener('click', function() {
      // Obtiene id del producto desde data attribute.
      const productId = this.dataset.productId;
      // Obtiene acción (block/unblock) desde data attribute.
      const action = this.dataset.action;
      // Envía petición POST al endpoint de acción sobre el producto.
      fetch(`/administrador/productos/${productId}/${action}/`, {
        // Define método HTTP.
        method: 'POST',
        // Incluye CSRF y tipo de contenido.
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Content-Type': 'application/json'
        }
      }).then(resp => {
        // Si fue exitoso, recarga para reflejar cambios.
        if (resp.ok) window.location.reload();
      });
    });
  });
});

// Función auxiliar para obtener CSRF desde cookies.
function getCSRFToken() {
  // Busca la cookie csrftoken.
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  // Retorna su valor o cadena vacía.
  return cookie ? cookie.split('=')[1] : '';
}
