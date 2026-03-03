document.addEventListener("DOMContentLoaded", function () {
  initializeNavbarMenuClose();
  initializeProductImageGallery();
  initializeSellerMessageModal();
  initializeAddToCartFromDescription();

  const getCookie = (name) => {
    const cookieValue = `; ${document.cookie}`;
    const cookieParts = cookieValue.split(`; ${name}=`);
    if (cookieParts.length === 2) {
      return cookieParts.pop().split(";").shift();
    }
    return "";
  };

  const showTemporaryAlert = (message, isError = false) => {
    const previous = document.getElementById("cart-temporary-alert");
    if (previous) {
      previous.remove();
    }

    const alertBox = document.createElement("div");
    alertBox.id = "cart-temporary-alert";
    alertBox.className = isError
      ? "cart-feedback__alert cart-feedback__alert--error"
      : "flash-product-created";
    alertBox.textContent = message;

    document.body.appendChild(alertBox);

    window.setTimeout(() => {
      if (!isError) {
        alertBox.classList.add("flash-product-created--hide");
      }
      window.setTimeout(() => {
        alertBox.remove();
      }, isError ? 0 : 250);
    }, 1500);
  };

  const requestProductQuantity = () => new Promise((resolve) => {
    const previous = document.getElementById("cart-feedback-quantity-modal");
    if (previous) {
      previous.remove();
    }

    const overlay = document.createElement("div");
    overlay.id = "cart-feedback-quantity-modal";
    overlay.className = "cart-feedback__overlay";

    overlay.innerHTML = `
      <div class="cart-feedback__modal" role="dialog" aria-modal="true" aria-labelledby="cart-feedback-modal-title">
        <h3 id="cart-feedback-modal-title" class="cart-feedback__title">Agregar al carrito</h3>
        <p class="cart-feedback__text">Digita la cantidad que deseas agregar</p>
        <input type="number" min="1" step="1" value="1" class="cart-feedback__input" id="cart-feedback-quantity-input" />
        <div class="cart-feedback__actions">
          <button type="button" class="cart-feedback__btn cart-feedback__btn--secondary" id="cart-feedback-cancel">Cancelar</button>
          <button type="button" class="cart-feedback__btn cart-feedback__btn--primary" id="cart-feedback-accept">Aceptar</button>
        </div>
      </div>
    `;

    const closeModal = (value) => {
      overlay.remove();
      resolve(value);
    };

    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) {
        closeModal(null);
      }
    });

    document.body.appendChild(overlay);

    const input = document.getElementById("cart-feedback-quantity-input");
    const acceptButton = document.getElementById("cart-feedback-accept");
    const cancelButton = document.getElementById("cart-feedback-cancel");

    if (!input || !acceptButton || !cancelButton) {
      closeModal(null);
      return;
    }

    input.focus();
    input.select();

    const accept = () => {
      const quantity = Number.parseInt(input.value, 10);
      closeModal(quantity);
    };

    acceptButton.addEventListener("click", accept);
    cancelButton.addEventListener("click", () => closeModal(null));
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        accept();
      }
      if (event.key === "Escape") {
        event.preventDefault();
        closeModal(null);
      }
    });
  });

  function initializeNavbarMenuClose() {
    document.addEventListener("click", function (event) {
      const menuDetails = document.querySelector(".nav-menu details");
      if (!menuDetails) {
        return;
      }
      if (!menuDetails.contains(event.target)) {
        menuDetails.removeAttribute("open");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") {
        return;
      }
      const menuDetails = document.querySelector(".nav-menu details");
      if (menuDetails) {
        menuDetails.removeAttribute("open");
      }
    });
  }

  // === Función para inicializar el cambio de imágenes ===
  function initializeProductImageGallery() {
    const mainImage = document.getElementById("main-image");
    const thumbnails = document.querySelectorAll(".product-view__thumbnail");

    if (!mainImage || thumbnails.length === 0) return;

    thumbnails.forEach((thumbnail) => {
      thumbnail.addEventListener("click", () => {
        // Cambiar la imagen principal
        mainImage.src = thumbnail.src;

        // Quitar borde activo de todas las miniaturas
        thumbnails.forEach((t) => t.classList.remove("product-view__thumbnail--active"));

        // Agregar borde activo a la seleccionada
        thumbnail.classList.add("product-view__thumbnail--active");

        // Pequeño efecto de transición (fade)
        mainImage.classList.add("fade");
        setTimeout(() => mainImage.classList.remove("fade"), 300);
      });
    });
  }

  function initializeSellerMessageModal() {
    const openButton = document.getElementById("open-seller-message-modal");
    const closeButton = document.getElementById("close-seller-message-modal");
    const backdrop = document.getElementById("seller-message-backdrop");
    const modal = document.getElementById("seller-message-modal");
    const messageForm = document.getElementById("seller-message-form");
    const messageText = document.getElementById("seller-message-text");

    if (!openButton || !closeButton || !backdrop || !modal || !messageForm || !messageText) {
      return;
    }

    const openModal = () => {
      modal.classList.add("seller-message-modal--open");
      modal.setAttribute("aria-hidden", "false");
      messageText.focus();
    };

    const closeModal = () => {
      modal.classList.remove("seller-message-modal--open");
      modal.setAttribute("aria-hidden", "true");
    };

    openButton.addEventListener("click", openModal);
    closeButton.addEventListener("click", closeModal);
    backdrop.addEventListener("click", closeModal);

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modal.classList.contains("seller-message-modal--open")) {
        closeModal();
      }
    });

    messageForm.addEventListener("submit", (event) => {
      event.preventDefault();

      const message = (messageText.value || "").trim();
      if (!message) {
        messageText.focus();
        return;
      }

      const endpoint = messageForm.dataset.endpoint;
      const productId = messageForm.dataset.productId;
      if (!endpoint || !productId) {
        return;
      }

      fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
        body: `product_id=${encodeURIComponent(productId)}&message=${encodeURIComponent(message)}`,
      })
        .then((response) => response.json().then((data) => ({ response, data })))
        .then(({ response, data }) => {
          if (!response.ok || !data.ok) {
            showTemporaryAlert(data?.message || "No se pudo enviar el mensaje.", true);
            return;
          }
          messageText.value = "";
          closeModal();
          showTemporaryAlert("Mensaje enviado exitosamente");
        })
        .catch(() => {
          showTemporaryAlert("Ocurrió un error al enviar el mensaje.", true);
        });
    });
  }

  function initializeAddToCartFromDescription() {
    const addButton = document.getElementById("add-to-cart-from-description");
    if (!addButton) {
      return;
    }

    addButton.addEventListener("click", async (event) => {
      event.preventDefault();

      const productId = addButton.dataset.productId;
      const endpoint = addButton.getAttribute("href");
      if (!productId || !endpoint) {
        return;
      }

      const quantity = await requestProductQuantity();
      if (quantity === null) {
        return;
      }

      if (Number.isNaN(quantity) || quantity <= 0) {
        showTemporaryAlert("Cantidad inválida.", true);
        return;
      }

      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
          body: `product_id=${encodeURIComponent(productId)}&quantity=${encodeURIComponent(quantity)}`,
        });

        const data = await response.json();
        if (!response.ok || !data.ok) {
          showTemporaryAlert(data.message || "No se pudo agregar el producto al carrito.", true);
          return;
        }

        showTemporaryAlert("Producto agregado exitosamente");
      } catch (error) {
        showTemporaryAlert("Ocurrió un error al agregar al carrito.", true);
      }
    });
  }
});
