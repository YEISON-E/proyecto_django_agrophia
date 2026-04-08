// Espera a que el contenido HTML esté completamente cargado.
document.addEventListener("DOMContentLoaded", function () {
  // Inicializa el cierre del menú de navegación al hacer clic fuera o presionar Escape.
  initializeNavbarMenuClose();
  // Inicializa la galería de imágenes del producto (miniaturas y vista principal).
  initializeProductImageGallery();
  // Inicializa el modal para enviar mensajes al vendedor.
  initializeSellerMessageModal();
  // Inicializa el flujo para agregar al carrito desde la vista de descripción.
  initializeAddToCartFromDescription();

  // Obtiene el valor de una cookie por nombre.
  const getCookie = (name) => {
    // Prepara la cadena de cookies con prefijo para facilitar el split.
    const cookieValue = `; ${document.cookie}`;
    // Divide por el patrón ; nombre= para intentar encontrar la cookie.
    const cookieParts = cookieValue.split(`; ${name}=`);
    // Si hay exactamente dos partes, la cookie fue encontrada.
    if (cookieParts.length === 2) {
      // Toma la parte final, corta hasta ; y retorna solo el valor.
      return cookieParts.pop().split(";").shift();
    }
    // Si no existe la cookie, retorna cadena vacía.
    return "";
  };

  // Muestra una alerta temporal en pantalla, de éxito o error.
  const showTemporaryAlert = (message, isError = false) => {
    // Busca si ya existe una alerta previa para reemplazarla.
    const previous = document.getElementById("cart-temporary-alert");
    // Si existe alerta anterior, la elimina antes de crear una nueva.
    if (previous) {
      previous.remove();
    }

    // Crea el contenedor de la nueva alerta.
    const alertBox = document.createElement("div");
    // Asigna id fijo para identificar esta alerta.
    alertBox.id = "cart-temporary-alert";
    // Asigna clase según sea alerta de error o de éxito.
    alertBox.className = isError
      ? "cart-feedback__alert cart-feedback__alert--error"
      : "flash-product-created";
    // Inserta el texto del mensaje.
    alertBox.textContent = message;

    // Agrega la alerta al body para hacerla visible.
    document.body.appendChild(alertBox);

    // Programa el cierre automático tras 4 segundos.
    window.setTimeout(() => {
      // Si no es error, aplica clase de salida para animación.
      if (!isError) {
        alertBox.classList.add("flash-product-created--hide");
      }
      // Elimina el nodo después de la animación (o de inmediato en error).
      window.setTimeout(() => {
        alertBox.remove();
      }, isError ? 0 : 250);
    }, 4000);
  };

  // Solicita al usuario una cantidad por medio de un modal y retorna una promesa con el valor.
  const requestProductQuantity = (maxStock) => new Promise((resolve) => {
    // Busca modal previo para evitar duplicados visuales.
    const previous = document.getElementById("cart-feedback-quantity-modal");
    // Si ya existe uno, lo remueve.
    if (previous) {
      previous.remove();
    }

    // Crea overlay del modal.
    const overlay = document.createElement("div");
    // Asigna id al overlay.
    overlay.id = "cart-feedback-quantity-modal";
    // Asigna clase de estilo del overlay.
    overlay.className = "cart-feedback__overlay";

    // Inserta la estructura interna del modal con título, input y acciones.
    overlay.innerHTML = `
      <div class="cart-feedback__modal" role="dialog" aria-modal="true" aria-labelledby="cart-feedback-modal-title">
        <h3 id="cart-feedback-modal-title" class="cart-feedback__title">Agregar al carrito</h3>
        <p class="cart-feedback__text">Digita la cantidad que deseas agregar</p>
        <input type="number" min="1" ${maxStock ? `max="${maxStock}"` : ""} step="1" value="1" class="cart-feedback__input" id="cart-feedback-quantity-input" />
        <div class="cart-feedback__actions">
          <button type="button" class="cart-feedback__btn cart-feedback__btn--secondary" id="cart-feedback-cancel">Cancelar</button>
          <button type="button" class="cart-feedback__btn cart-feedback__btn--primary" id="cart-feedback-accept">Aceptar</button>
        </div>
      </div>
    `;

    // Cierra modal y resuelve la promesa con el valor recibido.
    const closeModal = (value) => {
      // Elimina el overlay del DOM.
      overlay.remove();
      // Resuelve la promesa con cantidad o null.
      resolve(value);
    };

    // Permite cerrar si se hace clic sobre el fondo y no sobre el contenido interno.
    overlay.addEventListener("click", (event) => {
      // Si el clic fue exactamente en el overlay, cancela la operación.
      if (event.target === overlay) {
        closeModal(null);
      }
    });

    // Inserta el overlay en el documento para mostrar modal.
    document.body.appendChild(overlay);

    // Obtiene referencia al input de cantidad.
    const input = document.getElementById("cart-feedback-quantity-input");
    // Obtiene botón aceptar.
    const acceptButton = document.getElementById("cart-feedback-accept");
    // Obtiene botón cancelar.
    const cancelButton = document.getElementById("cart-feedback-cancel");

    // Si falta algún elemento crítico, cierra el modal y retorna null.
    if (!input || !acceptButton || !cancelButton) {
      closeModal(null);
      return;
    }

    // Lleva el foco al input para mejorar UX.
    input.focus();
    // Selecciona el valor inicial para facilitar reemplazo.
    input.select();

    // Acción de aceptar: parsea la cantidad e informa el valor al flujo.
    const accept = () => {
      // Convierte el valor escrito a entero base 10.
      const quantity = Number.parseInt(input.value, 10);
      // Cierra modal devolviendo la cantidad ingresada.
      closeModal(quantity);
    };

    // Vincula clic en aceptar con la acción de confirmar.
    acceptButton.addEventListener("click", accept);
    // Vincula clic en cancelar para cerrar sin cantidad.
    cancelButton.addEventListener("click", () => closeModal(null));
    // Maneja teclado del input para aceptar/cancelar rápidamente.
    input.addEventListener("keydown", (event) => {
      // Enter confirma la cantidad.
      if (event.key === "Enter") {
        // Evita submit implícito del formulario contenedor.
        event.preventDefault();
        // Ejecuta aceptación.
        accept();
      }
      // Escape cierra modal sin seleccionar cantidad.
      if (event.key === "Escape") {
        // Evita efectos por defecto de tecla.
        event.preventDefault();
        // Cierra con resultado nulo.
        closeModal(null);
      }
    });
  });

  // Inicializa comportamiento para cerrar el menú de navegación.
  function initializeNavbarMenuClose() {
    // Escucha clics globales para detectar clic fuera del menú.
    document.addEventListener("click", function (event) {
      // Selecciona el elemento details del menú.
      const menuDetails = document.querySelector(".nav-menu details");
      // Si no existe menú, no hay nada que cerrar.
      if (!menuDetails) {
        return;
      }
      // Si el clic ocurrió fuera del menú, lo cierra.
      if (!menuDetails.contains(event.target)) {
        menuDetails.removeAttribute("open");
      }
    });

    // Escucha teclado global para cerrar menú con Escape.
    document.addEventListener("keydown", function (event) {
      // Ignora teclas distintas de Escape.
      if (event.key !== "Escape") {
        return;
      }
      // Vuelve a seleccionar el menú details.
      const menuDetails = document.querySelector(".nav-menu details");
      // Si existe, quita atributo open para cerrarlo.
      if (menuDetails) {
        menuDetails.removeAttribute("open");
      }
    });
  }

  // Inicializa la galería de imágenes del producto.
  function initializeProductImageGallery() {
    // Obtiene imagen principal donde se mostrará la miniatura seleccionada.
    const mainImage = document.getElementById("main-image");
    // Obtiene todas las miniaturas disponibles.
    const thumbnails = document.querySelectorAll(".product-view__thumbnail");

    // Si falta imagen principal o no hay miniaturas, termina la función.
    if (!mainImage || thumbnails.length === 0) return;

    // Recorre cada miniatura para registrar su interacción.
    thumbnails.forEach((thumbnail) => {
      // Al hacer clic en miniatura, actualiza la imagen principal.
      thumbnail.addEventListener("click", () => {
        // Cambia la fuente de la imagen principal por la miniatura seleccionada.
        mainImage.src = thumbnail.src;

        // Quita estado activo de todas las miniaturas.
        thumbnails.forEach((t) => t.classList.remove("product-view__thumbnail--active"));

        // Marca como activa la miniatura seleccionada.
        thumbnail.classList.add("product-view__thumbnail--active");

        // Aplica efecto visual de transición en la imagen principal.
        mainImage.classList.add("fade");
        // Retira clase de fade tras 300 ms.
        setTimeout(() => mainImage.classList.remove("fade"), 300);
      });
    });
  }

  // Inicializa el modal de mensajería al vendedor.
  function initializeSellerMessageModal() {
    // Botón que abre el modal.
    const openButton = document.getElementById("open-seller-message-modal");
    // Botón que cierra el modal.
    const closeButton = document.getElementById("close-seller-message-modal");
    // Fondo del modal usado como backdrop.
    const backdrop = document.getElementById("seller-message-backdrop");
    // Contenedor principal del modal.
    const modal = document.getElementById("seller-message-modal");
    // Formulario de envío del mensaje.
    const messageForm = document.getElementById("seller-message-form");
    // Campo de texto del mensaje.
    const messageText = document.getElementById("seller-message-text");

    // Si falta cualquiera de los elementos, no se inicializa el módulo.
    if (!openButton || !closeButton || !backdrop || !modal || !messageForm || !messageText) {
      return;
    }

    // Función para abrir modal y enfocar textarea.
    const openModal = () => {
      // Activa clase de modal abierto.
      modal.classList.add("seller-message-modal--open");
      // Actualiza atributo de accesibilidad.
      modal.setAttribute("aria-hidden", "false");
      // Enfoca el campo de mensaje.
      messageText.focus();
    };

    // Función para cerrar modal.
    const closeModal = () => {
      // Quita clase de modal abierto.
      modal.classList.remove("seller-message-modal--open");
      // Actualiza atributo de accesibilidad.
      modal.setAttribute("aria-hidden", "true");
    };

    // Abre modal al hacer clic en el botón abrir.
    openButton.addEventListener("click", openModal);
    // Cierra modal al hacer clic en botón cerrar.
    closeButton.addEventListener("click", closeModal);
    // Cierra modal al hacer clic sobre el backdrop.
    backdrop.addEventListener("click", closeModal);

    // Permite cerrar modal con tecla Escape.
    document.addEventListener("keydown", (event) => {
      // Solo cierra si se presiona Escape y el modal está abierto.
      if (event.key === "Escape" && modal.classList.contains("seller-message-modal--open")) {
        closeModal();
      }
    });

    // Intercepta submit del formulario para enviar vía fetch.
    messageForm.addEventListener("submit", (event) => {
      // Evita recarga de página por submit tradicional.
      event.preventDefault();

      // Toma y limpia texto ingresado.
      const message = (messageText.value || "").trim();
      // Si está vacío, devuelve foco al campo y corta flujo.
      if (!message) {
        messageText.focus();
        return;
      }

      // Obtiene endpoint desde data attribute.
      const endpoint = messageForm.dataset.endpoint;
      // Obtiene id de producto desde data attribute.
      const productId = messageForm.dataset.productId;
      // Si faltan datos críticos, detiene envío.
      if (!endpoint || !productId) {
        return;
      }

      // Ejecuta petición POST al endpoint de mensajería.
      fetch(endpoint, {
        // Define método HTTP.
        method: "POST",
        // Define cabeceras necesarias para formulario y CSRF.
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
        // Envía product_id y mensaje codificados para URL.
        body: `product_id=${encodeURIComponent(productId)}&message=${encodeURIComponent(message)}`,
      })
        // Convierte respuesta a JSON y conserva también el objeto response.
        .then((response) => response.json().then((data) => ({ response, data })))
        // Evalúa resultado de negocio y estado HTTP.
        .then(({ response, data }) => {
          // Si falla HTTP o backend reporta ok=false, muestra error.
          if (!response.ok || !data.ok) {
            showTemporaryAlert(data?.message || "No se pudo enviar el mensaje.", true);
            return;
          }
          // Limpia el campo de mensaje al completar envío exitoso.
          messageText.value = "";
          // Cierra modal tras envío exitoso.
          closeModal();
          // Muestra confirmación al usuario.
          showTemporaryAlert("Mensaje enviado exitosamente");
        })
        // Captura cualquier error de red o parseo y muestra alerta.
        .catch(() => {
          showTemporaryAlert("Ocurrió un error al enviar el mensaje.", true);
        });
    });
  }

  // Inicializa flujo para agregar al carrito desde esta página.
  function initializeAddToCartFromDescription() {
    // Obtiene botón/enlace de agregar al carrito.
    const addButton = document.getElementById("add-to-cart-from-description");
    // Si no existe, no se inicializa este comportamiento.
    if (!addButton) {
      return;
    }

    // Maneja clic del botón para agregar producto.
    addButton.addEventListener("click", async (event) => {
      // Evita navegación normal del enlace.
      event.preventDefault();

      // Lee id del producto desde data attribute.
      const productId = addButton.dataset.productId;
      // Lee stock disponible y lo convierte a entero.
      const availableStock = Number.parseInt(addButton.dataset.productStock || "0", 10);
      // Obtiene endpoint desde href del enlace.
      const endpoint = addButton.getAttribute("href");
      // Si faltan datos esenciales, detiene el flujo.
      if (!productId || !endpoint) {
        return;
      }

      // Si no hay stock válido, informa y no permite continuar.
      if (Number.isNaN(availableStock) || availableStock <= 0) {
        showTemporaryAlert("Este producto no tiene stock disponible.", true);
        return;
      }

      // Solicita cantidad al usuario respetando el stock máximo.
      const quantity = await requestProductQuantity(availableStock);
      // Si usuario cancela el modal, termina sin enviar petición.
      if (quantity === null) {
        return;
      }

      // Valida que la cantidad sea numérica y positiva.
      if (Number.isNaN(quantity) || quantity <= 0) {
        showTemporaryAlert("Cantidad inválida.", true);
        return;
      }

      // Valida que la cantidad no exceda el stock disponible.
      if (quantity > availableStock) {
        showTemporaryAlert(`Solo hay ${availableStock} unidades disponibles.`, true);
        return;
      }

      // Bloque principal para envío al servidor y manejo de errores.
      try {
        // Envía POST para agregar producto al carrito con la cantidad elegida.
        const response = await fetch(endpoint, {
          // Define método HTTP.
          method: "POST",
          // Define cabeceras necesarias para request AJAX con CSRF.
          headers: {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
          // Envía product_id y quantity codificados.
          body: `product_id=${encodeURIComponent(productId)}&quantity=${encodeURIComponent(quantity)}`,
        });

        // Parsea la respuesta JSON del backend.
        const data = await response.json();
        // Si HTTP falla o backend responde ok=false, muestra error.
        if (!response.ok || !data.ok) {
          showTemporaryAlert(data.message || "No se pudo agregar el producto al carrito.", true);
          return;
        }

        // Muestra mensaje de éxito cuando la operación finaliza bien.
        showTemporaryAlert(data.message || "Producto agregado exitosamente");
      } catch (error) {
        // Si ocurre una excepción de red o ejecución, informa error genérico.
        showTemporaryAlert("Ocurrió un error al agregar al carrito.", true);
      }
    });
  }
});
