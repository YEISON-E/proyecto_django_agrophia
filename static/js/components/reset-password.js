// Validación en tiempo real para reset password
document.addEventListener('DOMContentLoaded', () => {
  // Mostrar/ocultar contraseña 1
  const checkbox1 = document.getElementById("toggle-password");
  const password = document.getElementById("id_password");

  if (checkbox1 && password) {
    checkbox1.addEventListener("change", () => {
      password.type = checkbox1.checked ? "text" : "password";
    });
  }

  // Mostrar/ocultar contraseña 2 (confirmar)
  const checkbox2 = document.getElementById("toggle-confirm-password");
  const confirmPassword = document.getElementById("id_confirm_password");

  if (checkbox2 && confirmPassword) {
    checkbox2.addEventListener("change", () => {
      confirmPassword.type = checkbox2.checked ? "text" : "password";
    });
  }

  // Validación en tiempo real del código
  const codigoInput = document.getElementById('id_codigo');
  const errorCodigo = document.getElementById('error-codigo');

  if (codigoInput && errorCodigo) {
    // Si hay error del servidor, mostrarlo
    if (errorCodigo.textContent.trim()) {
      errorCodigo.style.display = 'flex';
    }

    codigoInput.addEventListener('input', () => {
      const valor = codigoInput.value;
      let errorMsg = '';

      if (valor.length > 0) {
        if (/[^0-9]/.test(valor)) {
          errorMsg = 'Solo se permiten números';
        } else if (valor.length < 6) {
          errorMsg = 'El código debe tener 6 dígitos';
        } else if (valor.length > 6) {
          errorMsg = 'El código debe tener exactamente 6 dígitos';
        }
      }

      if (errorMsg) {
        errorCodigo.textContent = errorMsg;
        errorCodigo.style.display = 'flex';
      } else {
        errorCodigo.style.display = 'none';
      }
    });
  }

  // Validación en tiempo real de contraseña
  const passwordInput = document.getElementById('id_password');
  const errorPassword = document.getElementById('error-password');

  if (passwordInput && errorPassword) {
    if (errorPassword.textContent.trim()) {
      errorPassword.style.display = 'flex';
    }

    passwordInput.addEventListener('input', () => {
      const valor = passwordInput.value;
      let erroresList = [];

      if (valor.length > 0) {
        if (valor.length < 8) {
          erroresList.push('Mínimo 8 caracteres');
        }
        if (!/[A-Z]/.test(valor)) {
          erroresList.push('Requiere mayúscula');
        }
        if (!/[a-z]/.test(valor)) {
          erroresList.push('Requiere minúscula');
        }
        if (!/[0-9]/.test(valor)) {
          erroresList.push('Requiere número');
        }
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(valor)) {
          erroresList.push('Requiere carácter especial (!@#$%)');
        }
      }

      if (erroresList.length > 0) {
        // Crear lista HTML con los requisitos
        const listaHTML = erroresList
          .map(item => `<li>${item}</li>`)
          .join('');
        errorPassword.innerHTML = `<ul class="password-requirements">${listaHTML}</ul>`;
        errorPassword.style.display = 'flex';
      } else {
        errorPassword.style.display = 'none';
      }
    });
  }

  // Validación en tiempo real de confirmación de contraseña
  const confirmPasswordInput = document.getElementById('id_confirm_password');
  const errorConfirm = document.getElementById('error-confirm-password');

  if (confirmPasswordInput && errorConfirm && passwordInput) {
    if (errorConfirm.textContent.trim()) {
      errorConfirm.style.display = 'flex';
    }

    const checkPasswords = () => {
      const pass = passwordInput.value;
      const confirm = confirmPasswordInput.value;
      let errorMsg = '';

      if (confirm.length > 0 && pass !== confirm) {
        errorMsg = 'Las contraseñas no coinciden';
      }

      if (errorMsg) {
        errorConfirm.textContent = errorMsg;
        errorConfirm.style.display = 'flex';
      } else {
        errorConfirm.style.display = 'none';
      }
    };

    confirmPasswordInput.addEventListener('input', checkPasswords);
    passwordInput.addEventListener('input', checkPasswords);
  }
});

// Función para mostrar alerta de éxito
function mostrarAlertaExito(mensaje) {
  const alertaDiv = document.createElement('div');
  alertaDiv.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: linear-gradient(135deg, #4CAF50, #45a049);
    color: white;
    padding: 24px 32px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    font-size: 16px;
    font-weight: 500;
    z-index: 9999;
    animation: fadeIn 0.3s ease-out;
    max-width: 500px;
    text-align: center;
    word-wrap: break-word;
  `;
  alertaDiv.innerHTML = `✅ <br><br>${mensaje}`;
  document.body.appendChild(alertaDiv);

  // Remover alerta después de 5 segundos
  setTimeout(() => {
    alertaDiv.style.animation = 'fadeOut 0.3s ease-out';
    setTimeout(() => alertaDiv.remove(), 300);
  }, 5000);
}
