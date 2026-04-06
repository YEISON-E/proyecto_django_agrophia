document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("toolbar-shop-profile-toggle");
  const menu = document.getElementById("profile-dropdown");
  const reportTrigger = document.getElementById("toolbar-shop-report-trigger");
  const reportOverlay = document.getElementById("toolbar-shop-report-overlay");
  const reportClose = document.getElementById("toolbar-shop-report-close");
  const reportCancel = document.getElementById("toolbar-shop-report-cancel");
  const reportForm = document.getElementById("toolbar-shop-report-form");
  const reportScope = document.getElementById("toolbar-shop-report-scope");
  const individualSection = document.getElementById("toolbar-shop-individual-section");
  const generalSection = document.getElementById("toolbar-shop-general-section");
  const shopIdInput = document.getElementById("toolbar-shop-id-input");
  const shopIdHint = document.getElementById("toolbar-shop-id-hint");
  const departamentoSelect = document.getElementById("toolbar-shop-departamento");
  const municipioSelect = document.getElementById("toolbar-shop-municipio");
  const deptDataNode = document.getElementById("toolbar-shop-departamentos-data");
  const searchInput = document.getElementById("toolbar-shop-search-input");

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

  function resolveShopById(shopId) {
    const node = document.querySelector('.products-table__button--view[data-shop-id="' + shopId + '"]');
    if (!node) {
      return null;
    }
    return {
      id: shopId,
      name: (node.getAttribute("data-shop-name") || "").trim(),
    };
  }

  function updateShopSuggestion() {
    if (!shopIdInput || !shopIdHint) {
      return;
    }
    const raw = (shopIdInput.value || "").trim();
    if (!raw) {
      shopIdHint.textContent = "Escribe un ID y verás la sugerencia de la tienda.";
      return;
    }

    const shop = resolveShopById(raw);
    if (shop && shop.name) {
      shopIdHint.textContent = "Sugerencia: ID " + shop.id + " | " + shop.name;
    } else {
      shopIdHint.textContent = "No se encontró ese ID en la tabla actual. Igualmente puedes generarlo si existe en base de datos.";
    }
  }

  function updateScopeUI() {
    if (!reportScope || !individualSection || !generalSection) {
      return;
    }
    const isIndividual = reportScope.value === "individual";
    individualSection.hidden = !isIndividual;
    generalSection.hidden = isIndividual;

    if (shopIdInput) {
      shopIdInput.disabled = !isIndividual;
      if (!isIndividual) {
        shopIdInput.value = "";
      }
    }

    updateShopSuggestion();
  }

  function loadDepartamentosMunicipios() {
    if (!deptDataNode) {
      return {
        Caldas: [],
        Risaralda: [],
        "Quindío": [],
      };
    }
    try {
      return JSON.parse(deptDataNode.textContent || "{}");
    } catch (_error) {
      return {};
    }
  }

  function updateMunicipiosOptions() {
    if (!departamentoSelect || !municipioSelect) {
      return;
    }
    const departamentosMunicipios = loadDepartamentosMunicipios();
    const selectedDepartamento = departamentoSelect.value || "";
    const municipios = departamentosMunicipios[selectedDepartamento] || [];

    const previousValue = municipioSelect.value;
    municipioSelect.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = "Todos";
    municipioSelect.appendChild(allOption);

    municipios.forEach(function (municipio) {
      const option = document.createElement("option");
      option.value = municipio;
      option.textContent = municipio;
      municipioSelect.appendChild(option);
    });

    if (municipios.includes(previousValue)) {
      municipioSelect.value = previousValue;
    }
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
      updateShopSuggestion();
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
      if (shopIdInput && !isIndividual) {
        shopIdInput.value = "";
      }
    });
  }

  if (reportScope) {
    reportScope.addEventListener("change", updateScopeUI);
  }
  if (shopIdInput) {
    shopIdInput.addEventListener("input", updateShopSuggestion);
    shopIdInput.addEventListener("change", updateShopSuggestion);
  }

  if (departamentoSelect) {
    departamentoSelect.addEventListener("change", updateMunicipiosOptions);
  }

  setupTableSearch(searchInput, ".products-table__body tr");

  updateScopeUI();
  updateShopSuggestion();
  updateMunicipiosOptions();

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
