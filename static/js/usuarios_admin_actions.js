// Controla acciones de administración de usuarios: bloqueo y mensajería.

// Espera a que el DOM esté listo para inicializar eventos y modal.
document.addEventListener('DOMContentLoaded', function() {
    // Obtiene botón de mensaje masivo del toolbar.
    const toolbarMsgBtn = document.getElementById('toolbar-enviar-mensaje');
    // Si existe, registra clic para abrir modal en modo "todos".
    if (toolbarMsgBtn) {
      toolbarMsgBtn.addEventListener('click', function(e) {
        // Evita navegación por defecto del botón/enlace.
        e.preventDefault();
        // Abre modal sin usuario específico.
        openMessageModal('', 'Todos los usuarios');
      });
    }
  // Busca botones para bloquear/desbloquear usuarios.
  document.querySelectorAll('.users-table__button--block, .users-table__button--unblock').forEach(function(btn) {
    // Registra clic por cada botón de acción.
    btn.addEventListener('click', function() {
      // Obtiene id del usuario desde data attribute.
      const userId = this.dataset.userId;
      // Obtiene acción (block/unblock) desde data attribute.
      const action = this.dataset.action;
      // Envía petición POST de acción al endpoint admin.
      fetch(`/administrador/usuarios/${userId}/${action}/`, {
        // Define método HTTP.
        method: 'POST',
        // Incluye CSRF y tipo de contenido JSON.
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'Content-Type': 'application/json'
        }
      }).then(resp => {
        // Si operación fue correcta, recarga la página.
        if (resp.ok) window.location.reload();
      });
    });
  });

  // Crea el modal de mensajería y lo agrega al body.
  const modal = createMessageModal();
  document.body.appendChild(modal);

  // Busca botones de "enviar mensaje" por usuario.
  document.querySelectorAll('.users-table__button--message').forEach(function(btn) {
    // Registra clic para abrir modal dirigido a usuario específico.
    btn.addEventListener('click', function() {
      // Toma id de usuario objetivo.
      const userId = this.dataset.userId;
      // Toma nombre de usuario objetivo.
      const userName = this.dataset.userName;
      // Abre modal en modo individual.
      openMessageModal(userId, userName);
    });
  });
});

// Extrae token CSRF desde cookies del navegador.
function getCSRFToken() {
  // Busca cookie csrftoken en el string de cookies.
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  // Retorna token o vacío si no existe.
  return cookie ? cookie.split('=')[1] : '';
}

// Crea y configura el modal de envío de mensajes.
function createMessageModal() {
  // Crea contenedor raíz del modal.
  const modal = document.createElement('div');
  // Asigna id para localizarlo luego.
  modal.id = 'messageModal';
  // Lo inicializa oculto.
  modal.style.display = 'none';
  // Define el markup interno del modal.
  modal.innerHTML = `
    <div class="modal-bg" style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.25);z-index:1000;display:flex;align-items:center;justify-content:center;">
      <div class="modal-content" style="background:#fff;padding:24px 18px;border-radius:10px;min-width:320px;max-width:95vw;box-shadow:0 2px 16px 0 rgba(60,60,120,0.18);position:relative;">
        <button id="closeModalBtn" style="position:absolute;top:8px;right:12px;background:none;border:none;font-size:1.5em;color:#6366f1;cursor:pointer;">&times;</button>
        <h3 id="modalUserName" style="margin-bottom:10px;font-size:1.1em;color:#232323;font-weight:600;"></h3>
        <label for="modalRecipientSelect" style="font-weight:600;margin-bottom:6px;display:block;">Destinatario:</label>
        <select id="modalRecipientSelect" style="width:100%;margin-bottom:12px;padding:6px 8px;border-radius:6px;border:1px solid #d1d5db;">
          <option value="all">Todos</option>
          <option value="users">Solo usuarios</option>
          <option value="shops">Solo tiendas</option>
        </select>
        <textarea id="modalMessageText" rows="4" style="width:100%;border-radius:6px;border:1px solid #d1d5db;padding:8px 10px;margin-bottom:12px;"></textarea>
        <button id="sendMessageBtn" style="background:linear-gradient(90deg,#16a34a 60%,#4ade80 100%);color:#fff;border:none;border-radius:8px;padding:10px 28px;font-weight:700;font-size:1em;cursor:pointer;">Enviar mensaje</button>
      </div>
    </div>
  `;
  // Cierra modal al pulsar botón X.
  modal.querySelector('#closeModalBtn').onclick = () => { modal.style.display = 'none'; };
  // Cierra modal al hacer clic fuera del contenido.
  modal.querySelector('.modal-bg').onclick = (e) => { if (e.target === modal.querySelector('.modal-bg')) modal.style.display = 'none'; };
  // Maneja envío del mensaje desde el modal.
  modal.querySelector('#sendMessageBtn').onclick = function() {
    // Obtiene id de usuario objetivo (si aplica).
    const userId = modal.dataset.userId;
    // Obtiene texto del mensaje escrito.
    const message = modal.querySelector('#modalMessageText').value;
    // Obtiene destinatario (all/users/shops) para mensajes globales.
    const recipientType = modal.querySelector('#modalRecipientSelect').value;
    // Inicializa URL de envío.
    let url = '';
    // Inicializa cuerpo base con el mensaje.
    let body = { mensaje: message };
    // Si hay userId, envío individual.
    if (userId) {
      url = `/administrador/usuarios/${userId}/enviar_mensaje/`;
    } else {
      // Si no hay userId, envío general con tipo de destinatario.
      url = `/administrador/usuarios/enviar_mensaje/`;
      body.destinatario = recipientType;
    }
    // Ejecuta petición POST al endpoint seleccionado.
    fetch(url, {
      // Define método HTTP.
      method: 'POST',
      // Incluye CSRF y tipo de contenido JSON.
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      // Serializa body a JSON.
      body: JSON.stringify(body)
    }).then(resp => {
      // Si backend responde ok, cierra modal y muestra confirmación.
      if (resp.ok) {
        modal.style.display = 'none';
        showTemporaryAlert('Mensaje enviado con éxito', 1500);
      }
    });
  };
  // Retorna nodo modal completamente configurado.
  return modal;
}

// Abre modal y configura su contexto (individual o general).
function openMessageModal(userId, userName) {
  // Obtiene referencia al modal ya creado.
  const modal = document.getElementById('messageModal');
  // Muestra modal.
  modal.style.display = 'flex';
  // Guarda userId actual en data attribute.
  modal.dataset.userId = userId;
  // Actualiza título con el nombre de destinatario.
  modal.querySelector('#modalUserName').textContent = 'Mensaje para ' + userName;
  // Limpia textarea para nuevo mensaje.
  modal.querySelector('#modalMessageText').value = '';
  // Selecciona control de destinatario.
  const recipientSelect = modal.querySelector('#modalRecipientSelect');
  // Si es envío individual, oculta selector.
  if (userId) {
    recipientSelect.style.display = 'none';
  } else {
    // Si es envío general, muestra selector y pone valor por defecto.
    recipientSelect.style.display = 'block';
    recipientSelect.value = 'all';
  }
}

// Muestra alerta flotante temporal de confirmación.
function showTemporaryAlert(message, duration) {
  // Crea contenedor visual de alerta.
  let alertDiv = document.createElement('div');
  // Inserta el texto recibido.
  alertDiv.textContent = message;
  // Posiciona alerta fija en pantalla.
  alertDiv.style.position = 'fixed';
  alertDiv.style.top = '30px';
  alertDiv.style.left = '50%';
  alertDiv.style.transform = 'translateX(-50%)';
  alertDiv.style.background = 'linear-gradient(90deg,#16a34a 60%,#4ade80 100%)';
  alertDiv.style.color = '#fff';
  alertDiv.style.padding = '14px 32px';
  alertDiv.style.borderRadius = '8px';
  alertDiv.style.fontWeight = '700';
  alertDiv.style.fontSize = '1.1em';
  alertDiv.style.boxShadow = '0 2px 16px 0 rgba(60,60,120,0.18)';
  alertDiv.style.zIndex = '2000';
  alertDiv.style.opacity = '0';
  alertDiv.style.transition = 'opacity 0.3s';
  // Agrega alerta al DOM.
  document.body.appendChild(alertDiv);
  // Hace fade in inicial.
  setTimeout(() => { alertDiv.style.opacity = '1'; }, 10);
  // Programa fade out y eliminación final.
  setTimeout(() => {
    alertDiv.style.opacity = '0';
    setTimeout(() => { document.body.removeChild(alertDiv); }, 300);
  }, duration);
}
