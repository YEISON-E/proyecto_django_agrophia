// Función para inicializar el formulario de registro paso 1
function initializeRegisterStep1() {
  // Previsualización de foto cargada por el usuario
  const inputFoto = document.getElementById('input-foto');
  const hasTempPhotoInput = document.getElementById('has-temp-photo');
  if (inputFoto) {
    inputFoto.addEventListener('change', function(e) {
      if (e.target.files && e.target.files[0]) {
        const reader = new FileReader();
        reader.onload = function() {
          const preview = document.getElementById('preview');
          if (preview) {
            preview.src = reader.result;
            if (hasTempPhotoInput) {
              hasTempPhotoInput.value = '1';
            }
          }
        };
        reader.readAsDataURL(e.target.files[0]);
      }
    });
  }

  const documento = document.querySelector('input[name="documento"]');
  const nombres = document.querySelector('input[name="nombres"]');
  const apellidos = document.querySelector('input[name="apellidos"]');

  if (documento) {
    documento.addEventListener('input', function() {
      const error = validarDocumento(documento.value.trim());
      actualizarErrorEnInput(documento, error);
    });
  }

  if (nombres) {
    nombres.addEventListener('input', function() {
      const error = validarNombreApellido(nombres.value.trim(), 'nombre');
      actualizarErrorEnInput(nombres, error);
    });
  }

  if (apellidos) {
    apellidos.addEventListener('input', function() {
      const error = validarNombreApellido(apellidos.value.trim(), 'apellido');
      actualizarErrorEnInput(apellidos, error);
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
  if (!valor) {
    return 'Documento obligatorio.';
  }
  if (!/^\d+$/.test(valor)) {
    return 'Solo números.';
  }
  if (valor.length < 7) {
    return 'Documento muy corto.';
  }
  if (valor.length > 10) {
    return 'Documento muy largo.';
  }
  return '';
}

function validarNombreApellido(valor, campo) {
  const etiqueta = campo === 'apellido' ? 'apellido' : 'nombre';

  if (!valor) {
    return `${etiqueta.charAt(0).toUpperCase() + etiqueta.slice(1)} obligatorio.`;
  }
  if (valor.length < 2) {
    return `Minimo 2 caracteres.`;
  }
  if (valor.length > 40) {
    return `Maximo 40 caracteres.`;
  }
  if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s']+$/.test(valor)) {
    return `Solo letras y espacios.`;
  }
  return '';
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
  err.classList.add('is-visible');
  err.setAttribute('data-inline-error', 'true');
  err.textContent = mensaje;
  input.parentNode.appendChild(err);
}

function actualizarErrorEnInput(input, mensaje) {
  if (!input || !input.parentNode) return;

  const previo = input.parentNode.querySelector('.input-error[data-inline-error="true"]');
  if (previo) {
    previo.remove();
  }

  if (mensaje) {
    mostrarErrorEnInput(input, mensaje);
  }
}

// Función de validación para paso 1 del registro
function validarRegistroStep1(event) {
  const tdocumento = document.querySelector('select[name="tdocumento"]');
  const documento = document.querySelector('input[name="documento"]');
  const nombres = document.querySelector('input[name="nombres"]');
  const apellidos = document.querySelector('input[name="apellidos"]');
  const inputFoto = document.getElementById('input-foto');
  const hasTempPhotoInput = document.getElementById('has-temp-photo');
  const preview = document.getElementById('preview');
  const hasTempPhoto = hasTempPhotoInput && hasTempPhotoInput.value === '1';
  const hasPreviewPhoto = Boolean(preview && preview.src && !preview.src.includes('not-found.png'));

  limpiarErrores();
  let hayErrores = false;

  // Validar tipo de documento
  if (!tdocumento || !tdocumento.value) {
    mostrarErrorEnInput(tdocumento, 'Selecciona tipo de documento.');
    hayErrores = true;
  }

  // Validar número de documento
  const documentoError = validarDocumento(documento ? documento.value.trim() : '');
  if (documentoError) {
    mostrarErrorEnInput(documento, documentoError);
    hayErrores = true;
  }

  // Validar nombres
  const nombresError = validarNombreApellido(nombres ? nombres.value.trim() : '', 'nombre');
  if (nombresError) {
    mostrarErrorEnInput(nombres, nombresError);
    hayErrores = true;
  }

  // Validar apellidos
  const apellidosError = validarNombreApellido(apellidos ? apellidos.value.trim() : '', 'apellido');
  if (apellidosError) {
    mostrarErrorEnInput(apellidos, apellidosError);
    hayErrores = true;
  }

  // Validar foto obligatoria
  const hasNewPhoto = Boolean(inputFoto && inputFoto.files && inputFoto.files[0]);

  if (!hasNewPhoto && !hasTempPhoto && !hasPreviewPhoto) {
    mostrarErrorEnInput(inputFoto, 'Foto obligatoria.');
    hayErrores = true;
  } else if (hasNewPhoto && !validarFormatoFoto(inputFoto.files[0])) {
    mostrarErrorEnInput(inputFoto, 'Formato invalido (JPG, PNG, GIF o WebP).');
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