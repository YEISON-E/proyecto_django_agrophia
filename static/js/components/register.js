document.addEventListener('DOMContentLoaded', function() {
  // Mapa simple de departamentos -> municipios
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

  function poblarMunicipios() {
    const dep = departSelect.value;
    if (!munSelect) return;
    munSelect.innerHTML = '<option value="">Selecciona el Municipio</option>';
    if (!dep || !municipiosPorDepartamento[dep]) return;
    municipiosPorDepartamento[dep].forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      munSelect.appendChild(opt);
    });
  }

  if (departSelect && munSelect) {
    departSelect.addEventListener('change', poblarMunicipios);
  }

  // Mostrar/ocultar contraseña
  const mostrarChk = document.getElementById('mostrar');
  const passField = document.getElementById('password');
  const confirmField = document.querySelector('input[name="confirm_password"]');
  if (mostrarChk) {
    mostrarChk.addEventListener('change', function(){
      const tipo = this.checked ? 'text' : 'password';
      if(passField) passField.type = tipo;
      if(confirmField) confirmField.type = tipo;
    });
  }
});

// ===== VALIDACIONES INLINE =====

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

// Validar email
function validarEmail(valor) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
}

// Validar teléfono (exactamente 10 dígitos)
function validarTelefono(valor) {
  return /^\d{10}$/.test(valor);
}

// Validar contraseña (mínimo 8 caracteres, letras y números)
function validarPassword(valor) {
  return /(?=.*[A-Za-z])(?=.*\d).{8,}/.test(valor);
}

// Función principal de validación (llamada desde onsubmit)
function mostrarAlerta(event) {
  const email = document.querySelector('input[name="email"]');
  const telefono = document.querySelector('input[name="telefono"]');
  const departamento = document.querySelector('select[name="departamento"]');
  const municipio = document.querySelector('select[name="municipio"]');
  const direccion = document.querySelector('input[name="direccion"]');
  const password = document.querySelector('input[name="password"]');
  const confirm = document.querySelector('input[name="confirm_password"]');
  const descripcion = document.querySelector('textarea[name="descripcion"]');

  limpiarErrores();
  let hayErrores = false;

  // Validar correo
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

  // Validar departamento
  if (!departamento || !departamento.value) {
    mostrarErrorEnInput(departamento, 'Debes seleccionar un departamento.');
    hayErrores = true;
  }

  // Validar municipio
  if (!municipio || !municipio.value) {
    mostrarErrorEnInput(municipio, 'Debes seleccionar un municipio.');
    hayErrores = true;
  }

  // Validar dirección
  if (!direccion || !direccion.value.trim()) {
    mostrarErrorEnInput(direccion, 'La dirección es obligatoria.');
    hayErrores = true;
  }

  // Validar contraseña
  if (!password || !password.value) {
    mostrarErrorEnInput(password, 'La contraseña es obligatoria.');
    hayErrores = true;
  } else if (!validarPassword(password.value)) {
    mostrarErrorEnInput(password, 'La contraseña debe tener al menos 8 caracteres, incluyendo letras y números.');
    hayErrores = true;
  }

  // Validar confirmación de contraseña
  if (!confirm || !confirm.value) {
    mostrarErrorEnInput(confirm, 'Confirma la contraseña.');
    hayErrores = true;
  } else if (password && password.value !== confirm.value) {
    mostrarErrorEnInput(confirm, 'Las contraseñas no coinciden.');
    hayErrores = true;
  }

  // Validar descripción
  if (descripcion && descripcion.value.length > 40) {
    mostrarErrorEnInput(descripcion, 'La descripción no puede superar los 40 caracteres.');
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
window.mostrarAlerta = mostrarAlerta;

// ===== VALIDACIONES PARA PASO 1 (REGISTRO INICIAL) =====

// Validaciones para número de documento (paso 1)
function validarDocumento(valor) {
  // Solo números, longitud entre 7 y 8
  return /^\d{7,10}$/.test(valor);
}

// Validar formato de foto
function validarFormatoFoto(archivo) {
  const formatosValidos = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  return formatosValidos.includes(archivo.type);
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