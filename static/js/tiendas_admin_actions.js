// Define acciones AJAX para bloquear/desbloquear tiendas desde admin.
// Envía solicitud para bloquear la tienda indicada por id.
function bloquearTienda(id) {
  // Llama endpoint de bloqueo con CSRF.
  fetch(`/administrador/tiendas/${id}/block/`, {
    method: 'POST',
    headers: {'X-CSRFToken': getCSRFToken()},
    credentials: 'same-origin'
  })
    .then(function (r) {
      if (!r.ok) {
        throw new Error('No se pudo bloquear la tienda.');
      }
      return r.json();
    })
    .then(function (data) {
      if (data.ok) {
        location.reload();
      }
    })
    .catch(function (error) {
      console.error(error);
      alert('No se pudo bloquear la tienda. Intenta nuevamente.');
    });
}
// Envía solicitud para desbloquear la tienda indicada por id.
function desbloquearTienda(id) {
  // Llama endpoint de desbloqueo con CSRF.
  fetch(`/administrador/tiendas/${id}/unblock/`, {
    method: 'POST',
    headers: {'X-CSRFToken': getCSRFToken()},
    credentials: 'same-origin'
  })
    .then(function (r) {
      if (!r.ok) {
        throw new Error('No se pudo desbloquear la tienda.');
      }
      return r.json();
    })
    .then(function (data) {
      if (data.ok) {
        location.reload();
      }
    })
    .catch(function (error) {
      console.error(error);
      alert('No se pudo desbloquear la tienda. Intenta nuevamente.');
    });
}
// Obtiene token CSRF leyendo cookies del navegador.
function getCSRFToken() {
  // Nombre estándar de la cookie CSRF en Django.
  const name = 'csrftoken';
  // Separa todas las cookies por ';'.
  const cookies = document.cookie.split(';');
  // Recorre cada cookie para encontrar la que inicia con csrftoken=.
  for (let i = 0; i < cookies.length; i++) {
    let c = cookies[i].trim();
    if (c.startsWith(name + '=')) return c.substring(name.length + 1);
  }
  const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  if (metaToken) {
    return metaToken;
  }
  // Si no encuentra token, devuelve cadena vacía.
  return '';
}

// Espera DOM listo para enlazar acciones a botones de la tabla.
document.addEventListener('DOMContentLoaded', function () {
  // Busca botones con acción e id de tienda en data attributes.
  document.querySelectorAll('[data-shop-action][data-shop-id]').forEach(function (button) {
    // Registra clic para cada botón de acción.
    button.addEventListener('click', function () {
      // Obtiene tipo de acción (block/unblock).
      const action = button.getAttribute('data-shop-action');
      // Obtiene id de tienda objetivo.
      const id = button.getAttribute('data-shop-id');
      // Si no hay id válido, cancela la acción.
      if (!id) return;

      // Ejecuta bloqueo cuando acción sea block.
      if (action === 'block') {
        bloquearTienda(id);
        return;
      }
      // Ejecuta desbloqueo cuando acción sea unblock.
      if (action === 'unblock') {
        desbloquearTienda(id);
      }
    });
  });
});
