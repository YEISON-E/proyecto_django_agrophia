document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("toolbar-orders-profile-toggle");
  const menu = document.getElementById("profile-dropdown-orders");
  const reportTrigger = document.getElementById("toolbar-orders-report-trigger");
  const reportOverlay = document.getElementById("toolbar-orders-report-overlay");
  const reportClose = document.getElementById("toolbar-orders-report-close");
  const reportCancel = document.getElementById("toolbar-orders-report-cancel");
  const reportForm = document.getElementById("toolbar-orders-report-form");
  const reportScope = document.getElementById("toolbar-orders-report-scope");
  const individualSection = document.getElementById("toolbar-orders-individual-section");
  const generalSection = document.getElementById("toolbar-orders-general-section");
  const orderIdInput = document.getElementById("toolbar-orders-id-input");
  const orderIdHint = document.getElementById("toolbar-orders-id-hint");
  const searchInput = document.getElementById("toolbar-orders-search-input");

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

  function resolveOrderById(orderId) {
    const node = document.querySelector('.products-table__button--view[data-order-id="' + orderId + '"]');
    if (!node) {
      return null;
    }
    return {
      id: orderId,
      customer: (node.getAttribute("data-order-customer") || "").trim(),
      status: (node.getAttribute("data-order-status") || "").trim(),
    };
  }

  function updateOrderSuggestion() {
    if (!orderIdInput || !orderIdHint) {
      return;
    }
    const raw = (orderIdInput.value || "").trim();
    if (!raw) {
      orderIdHint.textContent = "Escribe un ID y verás la sugerencia del pedido.";
      return;
    }
    const order = resolveOrderById(raw);
    if (order && order.customer) {
      const statusLabel = order.status ? " | Estado: " + order.status : "";
      orderIdHint.textContent = "Sugerencia: Pedido #" + order.id + " | Cliente: " + order.customer + statusLabel;
    } else {
      orderIdHint.textContent = "No se encontró ese ID en la tabla actual. Igualmente puedes generarlo si existe en base de datos.";
    }
  }

  function updateScopeUI() {
    if (!reportScope || !individualSection || !generalSection) {
      return;
    }
    const isIndividual = reportScope.value === "individual";
    individualSection.hidden = !isIndividual;
    generalSection.hidden = isIndividual;

    if (orderIdInput) {
      orderIdInput.disabled = !isIndividual;
      if (!isIndividual) {
        orderIdInput.value = "";
      }
    }

    updateOrderSuggestion();
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
      updateOrderSuggestion();
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
      if (orderIdInput && !isIndividual) {
        orderIdInput.value = "";
      }
    });
  }

  if (reportScope) {
    reportScope.addEventListener("change", updateScopeUI);
  }
  if (orderIdInput) {
    orderIdInput.addEventListener("input", updateOrderSuggestion);
    orderIdInput.addEventListener("change", updateOrderSuggestion);
  }

  setupTableSearch(searchInput, ".products-table__body tr");

  updateScopeUI();
  updateOrderSuggestion();

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
