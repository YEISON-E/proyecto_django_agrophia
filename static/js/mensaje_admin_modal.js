// Espera a que el DOM esté listo para inicializar el modal de mensaje admin.
document.addEventListener('DOMContentLoaded', function() {
  // Busca el modal principal por su id.
  var modal = document.getElementById('adminMessageModal');
  // Solo continúa si el modal existe en la vista actual.
  if (modal) {
    // Muestra el modal al cargar la página.
    modal.style.display = 'flex';
    // Obtiene el id del mensaje desde data attribute.
    var mensajeId = modal.dataset.mensajeId;
    // Declara función auxiliar para marcar el mensaje como leído.
    function marcarLeido() {
      // Si no hay id de mensaje, no envía petición.
      if (!mensajeId) return;
      // Envía solicitud POST al endpoint de marcado.
      fetch('/usuarios/marcar-mensaje-admin-leido/', {
        // Define método HTTP.
        method: 'POST',
        // Incluye headers necesarios para CSRF y tipo de contenido.
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        // Envía el id del mensaje codificado en el body.
        body: 'mensaje_id=' + encodeURIComponent(mensajeId)
      });
    }
    // Cierra modal al hacer clic en el fondo, y marca como leído.
    modal.querySelector('.modal-bg').onclick = function(e) {
      // Solo cierra si el clic fue sobre el backdrop.
      if (e.target === this) {
        // Oculta el modal.
        modal.style.display = 'none';
        // Marca el mensaje como leído.
        marcarLeido();
      }
    };
    // Cierra modal al pulsar el botón de cerrar.
    modal.querySelector('.close-modal-btn').onclick = function() {
      // Oculta el modal.
      modal.style.display = 'none';
      // Marca el mensaje como leído.
      marcarLeido();
    };
  }
});

// Función auxiliar para extraer el token CSRF desde cookies.
function getCSRFToken() {
  // Busca la cookie csrftoken dentro del string de cookies.
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  // Retorna el valor del token o cadena vacía si no existe.
  return cookie ? cookie.split('=')[1] : '';
}
