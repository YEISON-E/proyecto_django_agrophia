// Acciones de la tabla de usuarios admin

document.addEventListener('DOMContentLoaded', function() {
    // Botón de enviar mensaje del toolbar (id único)
    const toolbarMsgBtn = document.getElementById('toolbar-enviar-mensaje');
    if (toolbarMsgBtn) {
      toolbarMsgBtn.addEventListener('click', function(e) {
        e.preventDefault();
        openMessageModal('', 'Todos los usuarios');
      });
    }
  // Bloquear/desbloquear usuario
  document.querySelectorAll('.users-table__button--block, .users-table__button--unblock').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const userId = this.dataset.userId;
      const action = this.dataset.action;
      fetch(`/administrador/usuarios/${userId}/${action}/`, {
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

  // Modal de mensajes
  const modal = createMessageModal();
  document.body.appendChild(modal);

  document.querySelectorAll('.users-table__button--message').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const userId = this.dataset.userId;
      const userName = this.dataset.userName;
      openMessageModal(userId, userName);
    });
  });
});

function getCSRFToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}

function createMessageModal() {
  const modal = document.createElement('div');
  modal.id = 'messageModal';
  modal.style.display = 'none';
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
  modal.querySelector('#closeModalBtn').onclick = () => { modal.style.display = 'none'; };
  modal.querySelector('.modal-bg').onclick = (e) => { if (e.target === modal.querySelector('.modal-bg')) modal.style.display = 'none'; };
  modal.querySelector('#sendMessageBtn').onclick = function() {
    const userId = modal.dataset.userId;
    const message = modal.querySelector('#modalMessageText').value;
    const recipientType = modal.querySelector('#modalRecipientSelect').value;
    let url = '';
    let body = { mensaje: message };
    if (userId) {
      url = `/administrador/usuarios/${userId}/enviar_mensaje/`;
    } else {
      url = `/administrador/usuarios/enviar_mensaje/`;
      body.destinatario = recipientType;
    }
    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    }).then(resp => {
      if (resp.ok) {
        modal.style.display = 'none';
        showTemporaryAlert('Mensaje enviado con éxito', 1500);
      }
    });
  };
  return modal;
}

function openMessageModal(userId, userName) {
  const modal = document.getElementById('messageModal');
  modal.style.display = 'flex';
  modal.dataset.userId = userId;
  modal.querySelector('#modalUserName').textContent = 'Mensaje para ' + userName;
  modal.querySelector('#modalMessageText').value = '';
  // Mostrar selector solo si es mensaje general
  const recipientSelect = modal.querySelector('#modalRecipientSelect');
  if (userId) {
    recipientSelect.style.display = 'none';
  } else {
    recipientSelect.style.display = 'block';
    recipientSelect.value = 'all';
  }
}

// Alerta flotante temporal
function showTemporaryAlert(message, duration) {
  let alertDiv = document.createElement('div');
  alertDiv.textContent = message;
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
  document.body.appendChild(alertDiv);
  setTimeout(() => { alertDiv.style.opacity = '1'; }, 10);
  setTimeout(() => {
    alertDiv.style.opacity = '0';
    setTimeout(() => { document.body.removeChild(alertDiv); }, 300);
  }, duration);
}
