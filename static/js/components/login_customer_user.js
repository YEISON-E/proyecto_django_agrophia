document.addEventListener("DOMContentLoaded", function () {
  const body = document.body;
  const loginUrl = body?.dataset.loginUrl;

  if (loginUrl) {
    window.history.replaceState(null, "", window.location.href);
    window.addEventListener("popstate", function () {
      window.location.href = loginUrl;
    });
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

  if (!searchInput || !cardsContainer || !cards.length) {
    return;
  }

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
