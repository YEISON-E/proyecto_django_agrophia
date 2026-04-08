// Script de apoyo para formulario de creacion de producto en admin.
document.addEventListener('DOMContentLoaded', function() {
  const maxImagenes = 8;
  const form = document.getElementById('product-create-form');
  const modal = document.getElementById('product-create-confirm-modal');
  const btnAccept = document.getElementById('product-create-confirm-accept');
  const btnCancel = document.getElementById('product-create-confirm-cancel');
  const backdrop = modal ? modal.querySelector('[data-product-create-confirm-close]') : null;
  const inputFotos = document.getElementById('fotos');
  const preview = document.getElementById('create-images-preview');
  const infoFotos = document.getElementById('create-images-info');
  let imagenesSeleccionadas = [];
  let envioConfirmado = false;

  const tipoSelect = document.getElementById('tipo');
  const tipoOtroGroup = document.getElementById('group-tipo-otro');
  if (tipoSelect && tipoOtroGroup) {
    tipoSelect.addEventListener('change', function() {
      if (this.value === 'Otros') {
        tipoOtroGroup.style.display = 'flex';
      } else {
        tipoOtroGroup.style.display = 'none';
      }
    });
  }

  function claveArchivo(file) {
    return [file.name, file.size, file.lastModified, file.type].join('|');
  }

  function sincronizarInputFotos() {
    if (!inputFotos) {
      return;
    }
    const dt = new DataTransfer();
    imagenesSeleccionadas.forEach(function(file) {
      dt.items.add(file);
    });
    inputFotos.files = dt.files;
  }

  function actualizarInfoFotos() {
    if (!infoFotos) {
      return;
    }
    infoFotos.classList.remove('is-error');
    infoFotos.textContent = 'Máximo 8 imágenes por producto. Seleccionadas: ' + imagenesSeleccionadas.length + '.';
  }

  function renderPreviewFotos() {
    if (!preview) {
      return;
    }
    preview.innerHTML = '';
    imagenesSeleccionadas.forEach(function(file, index) {
      const item = document.createElement('div');
      item.className = 'product-detail-image-item';

      const btnDelete = document.createElement('button');
      btnDelete.type = 'button';
      btnDelete.className = 'product-image-delete-btn';
      btnDelete.setAttribute('aria-label', 'Eliminar imagen');
      btnDelete.title = 'Eliminar imagen';
      btnDelete.textContent = '×';
      btnDelete.addEventListener('click', function() {
        imagenesSeleccionadas.splice(index, 1);
        sincronizarInputFotos();
        actualizarInfoFotos();
        renderPreviewFotos();
      });

      const img = document.createElement('img');
      img.className = 'product-new-image-item';
      img.alt = 'Previsualizacion imagen seleccionada';
      img.src = URL.createObjectURL(file);
      img.addEventListener('load', function() {
        URL.revokeObjectURL(img.src);
      });

      item.appendChild(btnDelete);
      item.appendChild(img);
      preview.appendChild(item);
    });
  }

  if (inputFotos && preview) {
    inputFotos.addEventListener('change', function() {
      const nuevas = Array.from(inputFotos.files || []).filter(function(file) {
        return (file.type || '').startsWith('image/');
      });
      const existentes = new Set(imagenesSeleccionadas.map(claveArchivo));

      nuevas.forEach(function(file) {
        const clave = claveArchivo(file);
        if (!existentes.has(clave)) {
          imagenesSeleccionadas.push(file);
          existentes.add(clave);
        }
      });

      if (imagenesSeleccionadas.length > maxImagenes) {
        imagenesSeleccionadas = imagenesSeleccionadas.slice(0, maxImagenes);
        if (infoFotos) {
          infoFotos.classList.add('is-error');
          infoFotos.textContent = 'Solo puedes seleccionar máximo 8 imágenes.';
        }
      }

      sincronizarInputFotos();
      renderPreviewFotos();
      if (imagenesSeleccionadas.length <= maxImagenes) {
        actualizarInfoFotos();
      }
    });
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
