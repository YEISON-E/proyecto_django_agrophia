// Define validación en tiempo real para el formulario de recuperación de contraseña.
// Espera a que el DOM esté completamente cargado antes de buscar elementos.
document.addEventListener('DOMContentLoaded', () => {
  // Obtiene referencia al input de correo por su id.
  const emailInput = document.getElementById('id_email');
  // Obtiene referencia al contenedor donde se muestra el error de correo.
  const errorEmail = document.getElementById('error-email');

  // Solo inicializa eventos si ambos elementos existen en la vista actual.
  if (emailInput && errorEmail) {
    // Si el backend ya dejó un mensaje de error, lo mantiene visible.
    if (errorEmail.textContent.trim()) {
      // Muestra el bloque de error usando display flex.
      errorEmail.style.display = 'flex';
    }

    // Escucha cambios en tiempo real cada vez que el usuario escribe.
    emailInput.addEventListener('input', () => {
      // Lee el valor actual del input eliminando espacios laterales.
      const valor = emailInput.value.trim();
      // Inicializa mensaje de error vacío (sin error por defecto).
      let errorMsg = '';

      // Si el campo está vacío, no muestra error en esta validación en vivo.
      if (valor.length === 0) {
        // Conserva mensaje vacío para ocultar el error.
        errorMsg = '';
      }
      // Si hay contenido y no cumple formato de correo, define mensaje de error.
      else if (!validarEmail(valor)) {
        // Mensaje mostrado cuando el correo no tiene formato válido.
        errorMsg = 'Correo electrónico inválido';
      }

      // Si existe mensaje de error, lo pinta y lo hace visible.
      if (errorMsg) {
        // Escribe el texto de error en el contenedor.
        errorEmail.textContent = errorMsg;
        // Muestra visualmente el bloque de error.
        errorEmail.style.display = 'flex';
      } else {
        // Si no hay error, oculta el contenedor de mensaje.
        errorEmail.style.display = 'none';
      }
    });
  }
});

// Declara función auxiliar para validar formato básico de email.
function validarEmail(email) {
  // Expresión regular simple para formato usuario@dominio.extensión.
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  // Retorna true si el email cumple el patrón, false en caso contrario.
  return regex.test(email);
}