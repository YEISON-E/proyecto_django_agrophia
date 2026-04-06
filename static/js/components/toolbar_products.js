document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("toolbar-products-profile-toggle");
  const menu = document.getElementById("profile-dropdown");
  const reportTrigger = document.getElementById("toolbar-products-report-trigger");
  const reportOverlay = document.getElementById("toolbar-products-report-overlay");
  const reportClose = document.getElementById("toolbar-products-report-close");
  const reportCancel = document.getElementById("toolbar-products-report-cancel");
  const reportForm = document.getElementById("toolbar-products-report-form");
  const reportScope = document.getElementById("toolbar-products-report-scope");
  const individualSection = document.getElementById("toolbar-products-individual-section");
  const generalSection = document.getElementById("toolbar-products-general-section");
  const productIdInput = document.getElementById("toolbar-products-id-input");
  const productIdHint = document.getElementById("toolbar-products-id-hint");
  const searchInput = document.getElementById("toolbar-products-search-input");

  function bindExclusiveFieldSelection(form) {
    if (!form) {
      return;
    }
    const allFieldsCheckbox = form.querySelector('input[name="all_fields"]');
    const fieldCheckboxes = Array.from(form.querySelectorAll('input[name="fields"]'));

    if (!allFieldsCheckbox || !fieldCheckboxes.length) {
      return;
    }

    function syncFromAll() {
      if (allFieldsCheckbox.checked) {
        fieldCheckboxes.forEach(function (checkbox) {
          checkbox.checked = false;
        });
      }
    }

    allFieldsCheckbox.addEventListener("change", syncFromAll);

    fieldCheckboxes.forEach(function (checkbox) {
      checkbox.addEventListener("change", function () {
        if (checkbox.checked) {
          allFieldsCheckbox.checked = false;
        }
      });
    });

    syncFromAll();
  }

  function normalizeSearchText(value) {
    return (value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function setupTableSearch(input, rowSelector) {
    if (!input) {
      return;
    }

    const rows = Array.from(document.querySelectorAll(rowSelector));
    if (!rows.length) {
      return;
    }

    input.addEventListener("input", function () {
      const query = normalizeSearchText(input.value);

      rows.forEach(function (row) {
        const rowText = normalizeSearchText(row.textContent);
        const shouldShow = !query || rowText.includes(query);
        row.style.display = shouldShow ? "" : "none";
      });
    });
  }

  if (!toggleButton || !menu) {
    return;
  }

  function closeReportModal() {
    if (!reportOverlay) {
      return;
    }
    reportOverlay.classList.remove("is-open");
    reportOverlay.setAttribute("aria-hidden", "true");
  }

  function openProfileMenu() {
    menu.style.display = "block";
    document.body.classList.add("admin-profile-menu-open");
  }

  function closeProfileMenu() {
    menu.style.display = "none";
    document.body.classList.remove("admin-profile-menu-open");
  }

  function resolveProductById(productId) {
    const node = document.querySelector('.products-table__button[data-product-id="' + productId + '"]');
    if (!node) {
      return null;
    }
    return {
      id: productId,
      name: (node.getAttribute("data-product-name") || "").trim(),
    };
  }

  function updateProductSuggestion() {
    if (!productIdInput || !productIdHint) {
      return;
    }
    const raw = (productIdInput.value || "").trim();
    if (!raw) {
      productIdHint.textContent = "Escribe un ID y verás la sugerencia del producto.";
      return;
    }

    const product = resolveProductById(raw);
    if (product && product.name) {
      productIdHint.textContent = "Sugerencia: ID " + product.id + " | " + product.name;
    } else {
      productIdHint.textContent = "No se encontró ese ID en la tabla actual. Igualmente puedes generarlo si existe en base de datos.";
    }
  }

  function updateScopeUI() {
    if (!reportScope || !individualSection || !generalSection) {
      return;
    }
    const isIndividual = reportScope.value === "individual";
    individualSection.hidden = !isIndividual;
    generalSection.hidden = isIndividual;

    if (productIdInput) {
      productIdInput.disabled = !isIndividual;
      if (!isIndividual) {
        productIdInput.value = "";
      }
    }

    updateProductSuggestion();
  }

  toggleButton.addEventListener("click", function (event) {
    event.stopPropagation();
    if (menu.style.display === "block") {
      closeProfileMenu();
      return;
    }
    openProfileMenu();
  });

  if (reportTrigger) {
    reportTrigger.addEventListener("click", function (event) {
      event.preventDefault();
      reportOverlay.classList.add("is-open");
      reportOverlay.setAttribute("aria-hidden", "false");
      updateScopeUI();
      updateProductSuggestion();
    });
  }
  if (reportClose) {
    reportClose.addEventListener("click", closeReportModal);
  }
  if (reportCancel) {
    reportCancel.addEventListener("click", closeReportModal);
  }
  if (reportForm) {
    reportForm.target = "_self";
    bindExclusiveFieldSelection(reportForm);
    reportForm.addEventListener("submit", function () {
      const isIndividual = reportScope && reportScope.value === "individual";
      if (productIdInput && !isIndividual) {
        productIdInput.value = "";
      }
    });
  }

  if (reportScope) {
    reportScope.addEventListener("change", updateScopeUI);
  }
  if (productIdInput) {
    productIdInput.addEventListener("input", updateProductSuggestion);
    productIdInput.addEventListener("change", updateProductSuggestion);
  }

  setupTableSearch(searchInput, ".products-table__body tr");

  updateScopeUI();
  updateProductSuggestion();

  window.addEventListener("click", function (event) {
    if (!event.target.closest(".toolbar-main__profile-dropdown")) {
      closeProfileMenu();
    }
    if (reportOverlay && event.target === reportOverlay) {
      closeReportModal();
    }
  });

  window.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeProfileMenu();
      closeReportModal();
    }
  });
});
