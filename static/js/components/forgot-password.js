// Validación en tiempo real para forgot-password
document.addEventListener('DOMContentLoaded', () => {
  const emailInput = document.getElementById('id_email');
  const errorEmail = document.getElementById('error-email');

  if (emailInput && errorEmail) {
    // Si hay error del servidor, mostrarlo
    if (errorEmail.textContent.trim()) {
      errorEmail.style.display = 'flex';
    }

    emailInput.addEventListener('input', () => {
      const valor = emailInput.value.trim();
      let errorMsg = '';

      // Validar que no esté vacío
      if (valor.length === 0) {
        errorMsg = '';
      }
      // Validar formato de email
      else if (!validarEmail(valor)) {
        errorMsg = 'Correo electrónico inválido';
      }

      if (errorMsg) {
        errorEmail.textContent = errorMsg;
        errorEmail.style.display = 'flex';
      } else {
        errorEmail.style.display = 'none';
      }
    });
  }
});

// Función para validar email
function validarEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}