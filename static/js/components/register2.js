/**
 * REGISTRO PASO 2 - VALIDACIÓN DE FORMULARIO
 * 
 * Este archivo contiene toda la lógica de validación para el segundo paso del registro:
 * - Validación de datos personales (email, teléfono, ubicación)
 * - Validación de contraseña con requisitos de fortaleza
 * - Población dinámica de departamentos y municipios
 * - Toggle de visibilidad de contraseña
 */

/**
 * Inicializa todos los event listeners del formulario de registro paso 2
 * Se ejecuta cuando el DOM está completamente cargado
 */
function initializeRegisterStep2() {
  // ===== CONFIGURACIÓN DE DEPARTAMENTOS Y MUNICIPIOS =====
  // Mapa que contiene la relación entre departamentos y sus municipios
  const municipiosPorDepartamento = {
    'Risaralda': [
      'Pereira','Dosquebradas','La Virginia','Apía','Balboa','Belén de Umbría','Guática','La Celia','Marsella','Mistrató','Pueblo Rico','Quinchía','Santa Rosa de Cabal','Santuario'
    ],
    'Caldas': [
      'Manizales','Aguadas','Anserma','Aranzazu','Belalcázar','Chinchiná','Filadelfia','La Dorada','La Merced','Manzanares','Marmato','Marquetalia','Marulanda','Neira','Norcasia','Pácora','Palestina','Pensilvania','Riosucio','Risaralda','Salamina','Samaná','San José','Supía','Victoria','Villamaría','Viterbo'
    ],
    'Quindio': [
      'Armenia','Buenavista','Calarcá','Circasia','Córdoba','Filandia','Génova','La Tebaida','Montenegro','Pijao','Quimbaya','Salento'
    ]
  };

  const departSelect = document.getElementById('input-departament');
  const munSelect = document.getElementById('input-municipality');

  /**
   * Llena el select de municipios basado en el departamento seleccionado
   * Se ejecuta cada vez que el usuario cambia el departamento
   */
  function poblarMunicipios() {
    const dep = departSelect.value;
    if (!munSelect) return;
    
    // Limpiar opciones previas
    munSelect.innerHTML = '<option value="">Selecciona el Municipio</option>';
    
    // Si no hay departamento seleccionado o no existe en el mapa, no hacer nada
    if (!dep || !municipiosPorDepartamento[dep]) return;
    
    // Agregar cada municipio como opción al select
    municipiosPorDepartamento[dep].forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      munSelect.appendChild(opt);
    });
  }

  // Agregar listener para cambios de departamento
  if (departSelect && munSelect) {
    departSelect.addEventListener('change', poblarMunicipios);
  }

  // ===== VALIDACIÓN DE CONTRASEÑA EN TIEMPO REAL =====
  // Obtener referencias de los campos de contraseña
  const passwordField = document.getElementById('id_password');
  const confirmPasswordField = document.getElementById('id_confirm_password');
  
  // Agregar validación en tiempo real mientras el usuario escribe
  if (passwordField) {
    passwordField.addEventListener('input', validarFortalezaContrasena);
  }

  if (confirmPasswordField) {
    confirmPasswordField.addEventListener('input', validarCoincidenciaContrasenas);
  }

  // ===== TOGGLE PASSWORD VISIBILITY =====
  // Elementos checkbox para mostrar/ocultar contraseña
  const togglePassword = document.getElementById('toggle-password');
  const toggleConfirmPassword = document.getElementById('toggle-confirm-password');

  // Cambiar tipo de input entre "password" y "text" al hacer click en checkbox
  if (togglePassword && passwordField) {
    togglePassword.addEventListener('change', function() {
      passwordField.type = this.checked ? 'text' : 'password';
    });
  }

  if (toggleConfirmPassword && confirmPasswordField) {
    toggleConfirmPassword.addEventListener('change', function() {
      confirmPasswordField.type = this.checked ? 'text' : 'password';
    });
  }
}

/**
 * Ejecutar la inicialización cuando el DOM esté listo
 * Detecta si el documento ya está cargado o espera a que lo esté
 */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeRegisterStep2);
} else {
  // Si el documento ya se cargó (con defer), ejecutar directamente
  initializeRegisterStep2();
}

// ===== FUNCIONES DE VALIDACIÓN =====

/**
 * Valida que el email tenga un formato correcto
 * @param {string} valor - El valor del email a validar
 * @returns {boolean} true si el email es válido
 */
function validarEmail(valor) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
}

/**
 * Valida que el teléfono tenga exactamente 10 dígitos
 * @param {string} valor - El valor del teléfono a validar
 * @returns {boolean} true si el teléfono tiene 10 dígitos
 */
function validarTelefono(valor) {
  return /^\d{10}$/.test(valor);
}

/**
 * Valida la fortaleza de la contraseña en tiempo real
 * Requiere: 8+ caracteres, mayúscula, minúscula, número y carácter especial
 * Muestra requisitos cumplidos (✓) y no cumplidos (✗) en una lista
 */
function validarFortalezaContrasena() {
  const password = document.getElementById('id_password');
  const errorDiv = document.getElementById('error-password');
  
  if (!password || !errorDiv) return;

  const valor = password.value;
  
  // Verificar cada requisito de seguridad
  const requisitos = {
    longitud: valor.length >= 8,                              // Mínimo 8 caracteres
    mayuscula: /[A-Z]/.test(valor),                           // Al menos una mayúscula
    minuscula: /[a-z]/.test(valor),                           // Al menos una minúscula
    numero: /[0-9]/.test(valor),                              // Al menos un número
    especial: /[!@#$%^&*(),.?":{}|<>]/.test(valor)            // Al menos un carácter especial
  };

  // Verificar si todos los requisitos se cumplen
  const todosValidos = Object.values(requisitos).every(req => req);

  // Si no hay contenido, ocultar el mensaje de validación
  if (valor.length === 0) {
    errorDiv.style.display = 'none';
    errorDiv.innerHTML = '';
    return;
  }

  // Construir lista HTML con cada requisito mostrando ✓ (cumplido) o ✗ (no cumplido)
  const requisitosLista = [
    `<li>${requisitos.longitud ? '✓' : '✗'} Mínimo 8 caracteres</li>`,
    `<li>${requisitos.mayuscula ? '✓' : '✗'} Requiere mayúscula</li>`,
    `<li>${requisitos.minuscula ? '✓' : '✗'} Requiere minúscula</li>`,
    `<li>${requisitos.numero ? '✓' : '✗'} Requiere número</li>`,
    `<li>${requisitos.especial ? '✓' : '✗'} Requiere carácter especial (!@#$%)</li>`
  ];

  // Si todos los requisitos se cumplen, ocultar el div de error
  if (todosValidos) {
    errorDiv.style.display = 'none';
    errorDiv.innerHTML = '';
  } else {
    // Si faltan requisitos, mostrar la lista HTML
    errorDiv.innerHTML = `<ul class="password-requirements">${requisitosLista.join('')}</ul>`;
    errorDiv.style.display = 'block';
  }
}

/**
 * Valida que las dos contraseñas coincidan en tiempo real
 * Se ejecuta mientras el usuario escribe en los campos de contraseña
 */
function validarCoincidenciaContrasenas() {
  const password = document.getElementById('id_password');
  const confirmPassword = document.getElementById('id_confirm_password');
  const errorDiv = document.getElementById('error-confirm-password');

  if (!confirmPassword || !errorDiv) return;

  // Si el campo de confirmación está vacío, no mostrar error
  if (confirmPassword.value.length === 0) {
    errorDiv.style.display = 'none';
    return;
  }

  // Comparar si las contraseñas no coinciden
  if (password && password.value !== confirmPassword.value) {
    errorDiv.innerHTML = 'Las contraseñas no coinciden';
    errorDiv.style.display = 'block';
  } else {
    // Si coinciden, ocultar el error
    errorDiv.style.display = 'none';
  }
}

/**
 * Limpia todos los mensajes de error generados dinámicamente
 * Excluye los divs de error de contraseña que se controlan por separado
 */
function limpiarErrores() {
  document.querySelectorAll('.input-error').forEach(el => {
    // No eliminar los divs de error de contraseña (son reutilizables)
    if (el.id !== 'error-password' && el.id !== 'error-confirm-password') {
      el.remove();
    }
  });
}

/**
 * Crea y muestra un mensaje de error debajo de un input
 * @param {Element} input - El elemento input donde mostrar el error
 * @param {string} mensaje - El mensaje de error a mostrar
 */
function mostrarErrorEnInput(input, mensaje) {
  if (!input || !input.parentNode) return;
  
  // Crear div con la clase de estilos para errores
  const err = document.createElement('div');
  err.className = 'input-error';
  err.textContent = mensaje;
  
  // Agregar el error debajo del input
  input.parentNode.appendChild(err);
}

// ===== VALIDACIÓN EN SUBMIT =====

/**
 * Función principal de validación del formulario
 * Se ejecuta cuando el usuario intenta enviar el formulario
 * Valida todos los campos y previene el envío si hay errores
 * @param {Event} event - El evento submit del formulario
 * @returns {boolean} false si hay errores y true si todo es válido
 */
function mostrarAlerta(event) {
  // Obtener referencias de todos los campos del formulario
  const email = document.querySelector('input[name="email"]');
  const telefono = document.querySelector('input[name="telefono"]');
  const departamento = document.querySelector('select[name="departamento"]');
  const municipio = document.querySelector('select[name="municipio"]');
  const direccion = document.querySelector('input[name="direccion"]');
  const password = document.getElementById('id_password');
  const confirm = document.getElementById('id_confirm_password');
  const descripcion = document.querySelector('textarea[name="descripcion"]');

  // Limpiar errores anteriores
  limpiarErrores();
  let hayErrores = false;

  // Validar email
  if (!email || !email.value.trim()) {
    mostrarErrorEnInput(email, 'El correo es obligatorio.');
    hayErrores = true;
  } else if (!validarEmail(email.value.trim())) {
    mostrarErrorEnInput(email, 'Correo inválido. Usa formato ejemplo@dominio.com');
    hayErrores = true;
  }

  // Validar teléfono
  if (!telefono || !telefono.value.trim()) {
    mostrarErrorEnInput(telefono, 'El teléfono es obligatorio.');
    hayErrores = true;
  } else if (!validarTelefono(telefono.value.trim())) {
    mostrarErrorEnInput(telefono, 'El teléfono debe tener exactamente 10 dígitos.');
    hayErrores = true;
  }

  // Validar que se haya seleccionado un departamento
  if (!departamento || !departamento.value) {
    mostrarErrorEnInput(departamento, 'Debes seleccionar un departamento.');
    hayErrores = true;
  }

  // Validar que se haya seleccionado un municipio
  if (!municipio || !municipio.value) {
    mostrarErrorEnInput(municipio, 'Debes seleccionar un municipio.');
    hayErrores = true;
  }

  // Validar que la dirección no esté vacía
  if (!direccion || !direccion.value.trim()) {
    mostrarErrorEnInput(direccion, 'La dirección es obligatoria.');
    hayErrores = true;
  }

  // Validar fortaleza de contraseña
  if (!password || !password.value) {
    if (document.getElementById('error-password')) {
      document.getElementById('error-password').innerHTML = 'La contraseña es obligatoria.';
      document.getElementById('error-password').style.display = 'block';
    }
    hayErrores = true;
  } else {
    // Verificar todos los requisitos de seguridad
    const requisitos = {
      longitud: password.value.length >= 8,
      mayuscula: /[A-Z]/.test(password.value),
      minuscula: /[a-z]/.test(password.value),
      numero: /[0-9]/.test(password.value),
      especial: /[!@#$%^&*(),.?":{}|<>]/.test(password.value)
    };

    const todosValidos = Object.values(requisitos).every(req => req);
    if (!todosValidos) {
      hayErrores = true;
    }
  }

  // Validar que la confirmación de contraseña no esté vacía
  if (!confirm || !confirm.value) {
    if (document.getElementById('error-confirm-password')) {
      document.getElementById('error-confirm-password').innerHTML = 'Confirma la contraseña.';
      document.getElementById('error-confirm-password').style.display = 'block';
    }
    hayErrores = true;
  } else if (password && password.value !== confirm.value) {
    // Validar que ambas contraseñas coincidan
    if (document.getElementById('error-confirm-password')) {
      document.getElementById('error-confirm-password').innerHTML = 'Las contraseñas no coinciden.';
      document.getElementById('error-confirm-password').style.display = 'block';
    }
    hayErrores = true;
  }

  // Validar que la descripción no exceda 40 caracteres
  if (descripcion && descripcion.value.length > 40) {
    mostrarErrorEnInput(descripcion, 'La descripción no puede superar los 40 caracteres.');
    hayErrores = true;
  }

  // Si hay errores, prevenir el envío del formulario
  if (hayErrores) {
    event.preventDefault();
    return false;
  }

  // Si todo es válido, permitir el envío
  return true;
}

/**
 * Exponer la función al alcance global para que pueda ser llamada desde el atributo
 * onsubmit del formulario HTML
 */
window.mostrarAlerta = mostrarAlerta;