// Acciones AJAX para bloquear/desbloquear tiendas
function bloquearTienda(id) {
  fetch(`/administrador/tiendas/${id}/block/`, {method: 'POST', headers: {'X-CSRFToken': getCSRFToken()}})
    .then(r => r.json()).then(data => { if(data.ok) location.reload(); });
}
function desbloquearTienda(id) {
  fetch(`/administrador/tiendas/${id}/unblock/`, {method: 'POST', headers: {'X-CSRFToken': getCSRFToken()}})
    .then(r => r.json()).then(data => { if(data.ok) location.reload(); });
}
function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    let c = cookies[i].trim();
    if (c.startsWith(name + '=')) return c.substring(name.length + 1);
  }
  return '';
}
