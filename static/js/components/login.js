// Mostrar alerta estilizada si hay error general de credenciales
document.addEventListener('DOMContentLoaded', () => {
  // Verificar si hay un elemento con error general
  const errorBox = document.querySelector('.error-box');
  if (errorBox) {
    const message = errorBox.textContent.trim();
    // Permitir HTML en el mensaje (para el link de registro)
    const messageHTML = errorBox.innerHTML.trim();
    mostrarAlerta(messageHTML);
  }

  // Validación en tiempo real del número de documento
  const usernameInput = document.getElementById('id_username');
  const errorUsername = document.getElementById('error-username');

  if (usernameInput && errorUsername) {
    // Si hay error del servidor, mostrarlo
    if (errorUsername.textContent.trim()) {
      errorUsername.style.display = 'flex';
    }

    usernameInput.addEventListener('input', () => {
      const valor = usernameInput.value;
      const tieneNoDigitos = /[^0-9]/.test(valor);
      let errorMsg = '';

      if (tieneNoDigitos) {
        errorMsg = 'Solo se permiten números';
      } else if (valor.length > 0 && valor.length < 8) {
        errorMsg = 'El documento debe tener entre 8 y 10 dígitos';
      } else if (valor.length > 10) {
        errorMsg = 'El documento debe tener entre 8 y 10 dígitos';
      }

      if (errorMsg) {
        errorUsername.textContent = errorMsg;
        errorUsername.style.display = 'flex';
      } else {
        errorUsername.style.display = 'none';
      }
    });
  }

  // Validación en tiempo real de contraseña
  const passwordInput = document.getElementById('id_password');
  const loginForm = document.querySelector('.login-form');
  
  if (passwordInput && loginForm) {
    let errorPassword = document.getElementById('error-password');
    if (!errorPassword) {
      errorPassword = document.createElement('div');
      errorPassword.id = 'error-password';
      errorPassword.className = 'input-error';
      errorPassword.style.display = 'none';
      passwordInput.parentElement.appendChild(errorPassword);
    }

    passwordInput.addEventListener('input', () => {
      const valor = passwordInput.value;
      if (valor.length > 0 && valor.length < 8) {
        errorPassword.textContent = 'La contraseña debe tener mínimo 8 caracteres';
        errorPassword.style.display = 'flex';
      } else {
        errorPassword.style.display = 'none';
      }
    });
  }

  // Mostrar/ocultar contraseña
  const checkbox = document.getElementById("toggle-password");
  const password = document.getElementById("id_password");

  if (checkbox && password) {
    checkbox.addEventListener("change", () => {
      password.type = checkbox.checked ? "text" : "password";
    });
  }
});

// Función para mostrar alerta estilizada
function mostrarAlerta(mensaje) {
  const alertaDiv = document.createElement('div');
  alertaDiv.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: linear-gradient(135deg, #ffffff);
    color: black;
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
  alertaDiv.innerHTML = `<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<i class="fas fa-exclamation-circle" style="color: blue;"></i><br>${mensaje} <br>`;
  document.body.appendChild(alertaDiv);

  // Remover alerta después de 5 segundos
  setTimeout(() => {
    alertaDiv.style.animation = 'fadeOut 0.3s ease-out';
    setTimeout(() => alertaDiv.remove(), 300);
  }, 5000);
}

// Agregar estilos de animación
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  @keyframes fadeOut {
    from {
      opacity: 1;
    }
    to {
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);
