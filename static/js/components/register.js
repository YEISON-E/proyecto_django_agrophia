// Función para inicializar el formulario de registro paso 1
function initializeRegisterStep1() {
  // Previsualización de foto cargada por el usuario
  const inputFoto = document.getElementById('input-foto');
  if (inputFoto) {
    inputFoto.addEventListener('change', function(e) {
      if (e.target.files && e.target.files[0]) {
        const reader = new FileReader();
        reader.onload = function() {
          const preview = document.getElementById('preview');
          if (preview) {
            preview.src = reader.result;
          }
        };
        reader.readAsDataURL(e.target.files[0]);
      }
    });
  }
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeRegisterStep1);
} else {
  // Si el documento ya se cargó, ejecutar directamente
  initializeRegisterStep1();
}

// ===== VALIDACIONES PARA PASO 1 (REGISTRO INICIAL) =====

// Validaciones para número de documento (paso 1)
function validarDocumento(valor) {
  // Solo números, longitud entre 7 y 10
  return /^\d{7,10}$/.test(valor);
}

// Validar formato de foto
function validarFormatoFoto(archivo) {
  const formatosValidos = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  return formatosValidos.includes(archivo.type);
}

// Limpiar errores inline
function limpiarErrores() {
  document.querySelectorAll('.input-error').forEach(el => el.remove());
}

// Mostrar error debajo del input
function mostrarErrorEnInput(input, mensaje) {
  if (!input || !input.parentNode) return;
  const err = document.createElement('div');
  err.className = 'input-error';
  err.textContent = mensaje;
  input.parentNode.appendChild(err);
}

// Función de validación para paso 1 del registro
function validarRegistroStep1(event) {
  const tdocumento = document.querySelector('select[name="tdocumento"]');
  const documento = document.querySelector('input[name="documento"]');
  const nombres = document.querySelector('input[name="nombres"]');
  const apellidos = document.querySelector('input[name="apellidos"]');
  const inputFoto = document.getElementById('input-foto');

  limpiarErrores();
  let hayErrores = false;

  // Validar tipo de documento
  if (!tdocumento || !tdocumento.value) {
    mostrarErrorEnInput(tdocumento, 'Selecciona un tipo de documento.');
    hayErrores = true;
  }

  // Validar número de documento
  if (!documento || !documento.value.trim()) {
    mostrarErrorEnInput(documento, 'El número de documento es obligatorio.');
    hayErrores = true;
  } else if (!validarDocumento(documento.value.trim())) {
    mostrarErrorEnInput(documento, 'El documento debe tener entre 7 y 10 dígitos.');
    hayErrores = true;
  }

  // Validar nombres
  if (!nombres || !nombres.value.trim()) {
    mostrarErrorEnInput(nombres, 'Los nombres son obligatorios.');
    hayErrores = true;
  }

  // Validar apellidos
  if (!apellidos || !apellidos.value.trim()) {
    mostrarErrorEnInput(apellidos, 'Los apellidos son obligatorios.');
    hayErrores = true;
  }

  // Validar foto obligatoria
  if (!inputFoto || !inputFoto.files || !inputFoto.files[0]) {
    mostrarErrorEnInput(inputFoto, 'La foto es obligatoria.');
    hayErrores = true;
  } else if (!validarFormatoFoto(inputFoto.files[0])) {
    mostrarErrorEnInput(inputFoto, 'Formato de foto inválido. Usa JPG, PNG, GIF o WebP.');
    hayErrores = true;
  }

  // Si hay errores, prevenir submit
  if (hayErrores) {
    event.preventDefault();
    return false;
  }

  return true;
}

// Hacer accesible desde onsubmit inline en la plantilla
window.validarRegistroStep1 = validarRegistroStep1;