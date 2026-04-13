document.addEventListener("DOMContentLoaded", () => {
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
    alertBox.className = `cart-feedback__alert ${isError ? "cart-feedback__alert--error" : "cart-feedback__alert--success"}`;
    alertBox.textContent = message;

    document.body.appendChild(alertBox);
    window.setTimeout(() => {
      alertBox.remove();
    }, 1500);
  };

  const requestProductQuantity = ({ productName, currentQuantity }) => new Promise((resolve) => {
    const previous = document.getElementById("cart-feedback-quantity-modal");
    if (previous) {
      previous.remove();
    }

    const overlay = document.createElement("div");
    overlay.id = "cart-feedback-quantity-modal";
    overlay.className = "cart-feedback__overlay";
    overlay.innerHTML = `
      <div class="cart-feedback__modal" role="dialog" aria-modal="true" aria-labelledby="cart-feedback-modal-title">
        <h3 id="cart-feedback-modal-title" class="cart-feedback__title">Cambiar cantidad</h3>
        <p class="cart-feedback__text">Escribe la nueva cantidad para ${productName}</p>
        <input type="number" min="1" step="1" value="${currentQuantity}" class="cart-feedback__input" id="cart-feedback-quantity-input" />
        <div class="cart-feedback__actions">
          <button type="button" class="cart-feedback__btn cart-feedback__btn--secondary" id="cart-feedback-cancel">Cancelar</button>
          <button type="button" class="cart-feedback__btn cart-feedback__btn--primary" id="cart-feedback-accept">Confirmar</button>
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

  // ── Pago ──────────────────────────────────────────────────
  const payCard  = document.getElementById("pay-card");
  const payNequi = document.getElementById("pay-nequi");
  const detailCard  = document.getElementById("detail-card");
  const detailNequi = document.getElementById("detail-nequi");

  function setSectionState(section, isVisible) {
    if (!section) {
      return;
    }

    section.hidden = !isVisible;
    section.querySelectorAll("input").forEach((input) => {
      input.disabled = !isVisible;
    });
  }

  function onPayChange() {
    if (payCard && payCard.checked) {
      setSectionState(detailCard, true);
      setSectionState(detailNequi, false);
    } else if (payNequi && payNequi.checked) {
      setSectionState(detailNequi, true);
      setSectionState(detailCard, false);
    } else {
      setSectionState(detailCard, false);
      setSectionState(detailNequi, false);
    }
  }

  if (payCard)  payCard.addEventListener("change", onPayChange);
  if (payNequi) payNequi.addEventListener("change", onPayChange);

  // ── Tarjeta preview en tiempo real ───────────────────────
  const cardNumber  = document.getElementById("card-number");
  const cardName    = document.getElementById("card-name");
  const cardExpiry  = document.getElementById("card-expiry");
  const displayNum  = document.getElementById("card-display-number");
  const displayName = document.getElementById("card-display-name");
  const displayExp  = document.getElementById("card-display-expiry");

  if (cardNumber) {
    cardNumber.addEventListener("input", () => {
      // Solo dígitos, grupos de 4
      let val = cardNumber.value.replace(/\D/g, "").slice(0, 16);
      cardNumber.value = val.replace(/(.{4})/g, "$1 ").trim();
      if (displayNum) {
        const padded = val.padEnd(16, "•");
        displayNum.textContent = padded.replace(/(.{4})/g, "$1 ").trim();
      }
    });
  }

  if (cardName) {
    cardName.addEventListener("input", () => {
      if (displayName) {
        displayName.textContent = cardName.value.toUpperCase() || "TITULAR";
      }
    });
  }

  if (cardExpiry) {
    cardExpiry.addEventListener("input", () => {
      let val = cardExpiry.value.replace(/\D/g, "").slice(0, 4);
      if (val.length > 2) val = val.slice(0, 2) + "/" + val.slice(2);
      cardExpiry.value = val;
      if (displayExp) displayExp.textContent = val || "MM/AA";
    });
  }

  // ── Entrega ───────────────────────────────────────────────
  const delStore = document.getElementById("del-store");
  const delHome  = document.getElementById("del-home");
  const detailStore = document.getElementById("detail-store");
  const detailHome  = document.getElementById("detail-home");
  const deliveryAddress = document.querySelector("input[name='delivery_address']");

  function onDeliveryChange() {
    if (delStore && delStore.checked) {
      setSectionState(detailStore, true);
      setSectionState(detailHome, false);
      if (deliveryAddress) {
        deliveryAddress.disabled = true;
      }
    } else if (delHome && delHome.checked) {
      setSectionState(detailHome, true);
      setSectionState(detailStore, false);
      if (deliveryAddress) {
        deliveryAddress.disabled = false;
      }
    } else {
      setSectionState(detailStore, false);
      setSectionState(detailHome, false);
      if (deliveryAddress) {
        deliveryAddress.disabled = true;
      }
    }
  }

  if (delStore) delStore.addEventListener("change", onDeliveryChange);
  if (delHome)  delHome.addEventListener("change", onDeliveryChange);

  // ── Validar antes de enviar ───────────────────────────────
  const form = document.getElementById("cart-checkout-form");
  const quantityButtons = document.querySelectorAll("[data-quantity-trigger]");

  quantityButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      const productName = button.dataset.productName || "este producto";
      const currentQuantity = button.dataset.currentQuantity || "1";
      const availableStock = Number.parseInt(button.dataset.availableStock || "0", 10);
      const endpoint = button.dataset.updateEndpoint;

      const quantity = await requestProductQuantity({ productName, currentQuantity });
      if (quantity === null) {
        return;
      }

      if (!Number.isInteger(quantity) || quantity < 1) {
        showTemporaryAlert("Ingresa una cantidad valida mayor que 0.", true);
        return;
      }

      if (Number.isInteger(availableStock) && availableStock >= 0 && quantity > availableStock) {
        showTemporaryAlert(`Solo hay ${availableStock} unidades disponibles para este producto.`, true);
        return;
      }

      if (!endpoint) {
        showTemporaryAlert("No se pudo actualizar la cantidad.", true);
        return;
      }

      const payload = new URLSearchParams();
      payload.append(`quantity_${button.dataset.productId}`, String(quantity));

      fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
        body: payload.toString(),
      })
        .then((response) => response.json().then((data) => ({ response, data })))
        .then(({ response, data }) => {
          if (!response.ok || !data.ok) {
            showTemporaryAlert(data?.message || "No se pudo actualizar la cantidad.", true);
            return;
          }
          showTemporaryAlert(data.message || "Cantidad actualizada.");
          window.setTimeout(() => {
            window.location.reload();
          }, 300);
        })
        .catch(() => {
          showTemporaryAlert("Ocurrio un error al actualizar la cantidad.", true);
        });
    });
  });

  if (form) {
    form.addEventListener("submit", (e) => {
      const submitter = e.submitter;
      if (submitter && submitter.hasAttribute("formnovalidate")) {
        return;
      }

      const paySelected = document.querySelector("input[name='payment_method']:checked");
      const delSelected = document.querySelector("input[name='delivery_method']:checked");

      if (!paySelected) {
        e.preventDefault();
        alert("Selecciona un método de pago.");
        return;
      }
      if (!delSelected) {
        e.preventDefault();
        alert("Selecciona un método de entrega.");
        return;
      }
      if (delSelected.value === "Envío a domicilio") {
        const addr = form.querySelector("input[name='delivery_address']");
        if (!addr || !addr.value.trim()) {
          e.preventDefault();
          alert("Ingresa la dirección de entrega.");
          addr && addr.focus();
          return;
        }
      }
    });
  }

  onPayChange();
  onDeliveryChange();
});
