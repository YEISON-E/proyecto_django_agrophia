// Script de apoyo para formulario de edición de producto en admin.
// Espera la carga completa del DOM.
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('product-edit-form');
  const modal = document.getElementById('product-edit-confirm-modal');
  const btnAccept = document.getElementById('product-edit-confirm-accept');
  const btnCancel = document.getElementById('product-edit-confirm-cancel');
  const backdrop = modal ? modal.querySelector('[data-product-confirm-close]') : null;
  let envioConfirmado = false;

  // Obtiene select del tipo de producto.
  const tipoSelect = document.getElementById('tipo');
  // Obtiene contenedor del campo "otro tipo".
  const tipoOtroGroup = document.getElementById('group-tipo-otro');
  // Solo registra eventos si ambos elementos existen.
  if (tipoSelect && tipoOtroGroup) {
    // Al cambiar el tipo, muestra u oculta campo adicional.
    tipoSelect.addEventListener('change', function() {
      // Si selecciona "Otros", muestra el campo extra.
      if (this.value === 'Otros') {
        tipoOtroGroup.style.display = 'block';
      } else {
        // Para cualquier otro valor, oculta el campo extra.
        tipoOtroGroup.style.display = 'none';
      }
    });
  }

  // Marca para eliminar una imagen actual al hacer click en la X y la oculta de inmediato.
  document.querySelectorAll('[data-image-delete]').forEach(function(deleteBtn) {
    deleteBtn.addEventListener('click', function() {
      const imageItem = deleteBtn.closest('[data-image-item]');
      if (!imageItem) {
        return;
      }

      const deleteInput = imageItem.querySelector('.product-image-delete-input');
      if (!deleteInput) {
        return;
      }

      deleteInput.checked = true;
      imageItem.classList.add('is-marked-delete');
      actualizarLimiteYPrevisualizacion();
    });
  });

  const maxTotalImagenes = 8;
  const inputNuevas = document.getElementById('new-images-input');
  const previewNuevas = document.getElementById('new-images-preview');
  const infoLimite = document.getElementById('images-limit-info');
  let nuevasImagenesAcumuladas = [];

  function contarExistentesNoEliminadas() {
    const items = document.querySelectorAll('[data-image-item]');
    let total = 0;
    items.forEach(function(item) {
      const deleteInput = item.querySelector('.product-image-delete-input');
      if (deleteInput && !deleteInput.checked) {
        total += 1;
      }
    });
    return total;
  }

  function renderPreview(files) {
    if (!previewNuevas) {
      return;
    }

    previewNuevas.innerHTML = '';
    Array.from(files).forEach(function(file) {
      if (!(file.type || '').startsWith('image/')) {
        return;
      }
      const img = document.createElement('img');
      img.className = 'product-new-image-item';
      img.alt = 'Previsualizacion nueva imagen';
      img.src = URL.createObjectURL(file);
      img.addEventListener('load', function() {
        URL.revokeObjectURL(img.src);
      });
      previewNuevas.appendChild(img);
    });
  }

  function obtenerClaveArchivo(file) {
    return [file.name, file.size, file.lastModified, file.type].join('|');
  }

  function sincronizarInputConAcumuladas() {
    if (!inputNuevas) {
      return;
    }
    const dt = new DataTransfer();
    nuevasImagenesAcumuladas.forEach(function(file) {
      dt.items.add(file);
    });
    inputNuevas.files = dt.files;
  }

  function actualizarLimiteYPrevisualizacion() {
    if (!inputNuevas) {
      return;
    }

    const existentes = contarExistentesNoEliminadas();
    const disponibles = Math.max(0, maxTotalImagenes - existentes);
    if (nuevasImagenesAcumuladas.length > disponibles) {
      nuevasImagenesAcumuladas = nuevasImagenesAcumuladas.slice(0, disponibles);
      if (infoLimite) {
        infoLimite.textContent = 'Solo puedes seleccionar ' + disponibles + ' imagen(es) adicional(es) para completar el máximo de 8.';
        infoLimite.classList.add('is-error');
      }
    } else if (infoLimite) {
      infoLimite.textContent = 'Máximo 8 imágenes en total. Puedes agregar una por una. Disponibles: ' + disponibles + '. Seleccionadas: ' + nuevasImagenesAcumuladas.length + '.';
      infoLimite.classList.remove('is-error');
    }

    sincronizarInputConAcumuladas();
    renderPreview(nuevasImagenesAcumuladas);
  }

  if (inputNuevas) {
    inputNuevas.addEventListener('change', function() {
      const nuevasSeleccionadas = Array.from(inputNuevas.files || []).filter(function(file) {
        return (file.type || '').startsWith('image/');
      });

      const existentesPorClave = new Set(nuevasImagenesAcumuladas.map(obtenerClaveArchivo));
      nuevasSeleccionadas.forEach(function(file) {
        const clave = obtenerClaveArchivo(file);
        if (!existentesPorClave.has(clave)) {
          nuevasImagenesAcumuladas.push(file);
          existentesPorClave.add(clave);
        }
      });

      actualizarLimiteYPrevisualizacion();
    });
    actualizarLimiteYPrevisualizacion();
  }

  if (form && modal && btnAccept && btnCancel) {
    const abrir = function() {
      modal.setAttribute('aria-hidden', 'false');
      btnAccept.focus();
    };

    const cerrar = function() {
      modal.setAttribute('aria-hidden', 'true');
    };

    form.addEventListener('submit', function(event) {
      if (envioConfirmado) {
        envioConfirmado = false;
        return;
      }
      event.preventDefault();
      abrir();
    });

    btnAccept.addEventListener('click', function() {
      cerrar();
      envioConfirmado = true;
      form.requestSubmit();
    });

    btnCancel.addEventListener('click', cerrar);
    if (backdrop) {
      backdrop.addEventListener('click', cerrar);
    }

    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape' && modal.getAttribute('aria-hidden') === 'false') {
        cerrar();
      }
    });
  }
});
