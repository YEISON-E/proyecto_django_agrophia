document.addEventListener("DOMContentLoaded", function () {
  const body = document.body;
  const loginUrl = body?.dataset.loginUrl;

  if (loginUrl) {
    window.history.replaceState(null, "", window.location.href);
    window.addEventListener("popstate", function () {
      window.location.href = loginUrl;
    });
  }

  const customerHomeNotice = document.getElementById("customer-home-notice");
  if (customerHomeNotice) {
    const noticeTotalDurationMs = 4000;
    const noticeFadeDurationMs = 250;

    window.setTimeout(() => {
      customerHomeNotice.classList.add("flash-product-created--hide");
      window.setTimeout(() => {
        customerHomeNotice.remove();
      }, noticeFadeDurationMs);
    }, noticeTotalDurationMs - noticeFadeDurationMs);
  }

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

  const searchInput = document.querySelector(".search-home__bar");
  const filterIcon = document.querySelector(".search-home__filter__icon");
  const filterPanel = document.getElementById("search-home-filter-panel");
  const filterTypeSelect = document.getElementById("filter-product-type");
  const filterUnitSelect = document.getElementById("filter-product-unit");
  const filterOrderSelect = document.getElementById("filter-product-order");
  const filterConfirmBtn = document.getElementById("filter-confirm-btn");
  const categoryOptions = document.querySelectorAll(".list-home__option");
  const cardsContainer = document.querySelector(".card-home__container");
  const cards = cardsContainer ? Array.from(cardsContainer.querySelectorAll(".card-home")) : [];
  const addToCartButtons = document.querySelectorAll(".btn-agregar-carrito");

  if (!searchInput || !cardsContainer || !cards.length) {
    return;
  }

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
    }, 4000);
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

  addToCartButtons.forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.preventDefault();

      const productId = button.dataset.productId;
      const endpoint = button.getAttribute("href");

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

        showTemporaryAlert(data.message || "Producto agregado exitosamente");
      } catch (error) {
        showTemporaryAlert("Ocurrió un error al agregar al carrito.", true);
      }
    });
  });

  let selectedCategory = "";
  let selectedType = "";
  let selectedUnit = "";
  let sortMode = "none";

  const updateFilterIconState = () => {
    if (!filterIcon) {
      return;
    }
    const hasActiveFilter = selectedType || selectedUnit || sortMode !== "none";
    filterIcon.classList.toggle("search-home__filter__icon--active", Boolean(hasActiveFilter));
  };

  const getCardPrice = (card) => {
    const raw = (card.dataset.price || "0").replace(",", ".");
    const parsed = Number(raw);
    return Number.isNaN(parsed) ? 0 : parsed;
  };

  const ensureEmptyResultElement = () => {
    let emptyResult = document.getElementById("card-home-search-empty");
    if (!emptyResult) {
      emptyResult = document.createElement("p");
      emptyResult.id = "card-home-search-empty";
      emptyResult.className = "card-home__empty";
      emptyResult.textContent = "No se encontraron productos con esos filtros.";
      emptyResult.style.display = "none";
      cardsContainer.appendChild(emptyResult);
    }
    return emptyResult;
  };

  const emptyResult = ensureEmptyResultElement();

  const applyFilters = () => {
    const query = (searchInput.value || "").trim().toLowerCase();

    const filteredCards = cards.filter((card) => {
      const cardName = card.dataset.name || "";
      const cardCategory = card.dataset.category || "";
      const cardType = card.dataset.type || "";
      const cardUnit = card.dataset.unit || "";

      const matchesQuery = !query
        || cardName.includes(query)
        || cardType.includes(query)
        || cardUnit.includes(query);

      const matchesCategory = !selectedCategory || cardCategory === selectedCategory;
      const matchesType = !selectedType || cardCategory === selectedType || cardType === selectedType;
      const matchesUnit = !selectedUnit || cardUnit === selectedUnit;

      return matchesQuery && matchesCategory && matchesType && matchesUnit;
    });

    const sortedCards = [...filteredCards];
    if (sortMode === "price-asc") {
      sortedCards.sort((left, right) => getCardPrice(left) - getCardPrice(right));
    } else if (sortMode === "price-desc") {
      sortedCards.sort((left, right) => getCardPrice(right) - getCardPrice(left));
    }

    cards.forEach((card) => {
      card.style.display = "none";
    });

    sortedCards.forEach((card) => {
      card.style.display = "block";
      cardsContainer.appendChild(card);
    });

    emptyResult.style.display = sortedCards.length ? "none" : "block";
  };

  searchInput.addEventListener("input", applyFilters);

  categoryOptions.forEach((option) => {
    option.addEventListener("click", () => {
      const clickedCategory = (option.textContent || "").trim().toLowerCase();

      if (selectedCategory === clickedCategory) {
        selectedCategory = "";
        option.classList.remove("list-home__option--active");
      } else {
        selectedCategory = clickedCategory;
        categoryOptions.forEach((item) => item.classList.remove("list-home__option--active"));
        option.classList.add("list-home__option--active");
      }

      applyFilters();
    });
  });

  if (filterIcon && filterPanel) {
    filterIcon.addEventListener("click", (event) => {
      event.stopPropagation();

      if (filterTypeSelect) {
        filterTypeSelect.value = selectedType;
      }
      if (filterUnitSelect) {
        filterUnitSelect.value = selectedUnit;
      }
      if (filterOrderSelect) {
        filterOrderSelect.value = sortMode;
      }

      filterPanel.style.display = filterPanel.style.display === "none" ? "flex" : "none";
    });
  }

  if (filterConfirmBtn) {
    filterConfirmBtn.addEventListener("click", () => {
      selectedType = (filterTypeSelect?.value || "").trim().toLowerCase();
      selectedUnit = (filterUnitSelect?.value || "").trim().toLowerCase();
      sortMode = (filterOrderSelect?.value || "none").trim();

      if (filterPanel) {
        filterPanel.style.display = "none";
      }

      updateFilterIconState();
      applyFilters();
    });
  }

  document.addEventListener("click", (event) => {
    if (!filterPanel || !filterIcon) {
      return;
    }

    if (filterPanel.style.display === "none") {
      return;
    }

    const clickedInsidePanel = filterPanel.contains(event.target);
    const clickedOnIcon = filterIcon.contains(event.target);

    if (!clickedInsidePanel && !clickedOnIcon) {
      filterPanel.style.display = "none";
    }
  });

  updateFilterIconState();

  if (filterPanel) {
    filterPanel.style.display = "none";
  }

  applyFilters();
});
