document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("toolbar-users-profile-toggle");
    const menu = document.getElementById("profile-dropdown");
    const reportTrigger = document.getElementById("toolbar-users-report-trigger");
    const reportTriggers = [
        reportTrigger,
        ...Array.from(document.querySelectorAll(".js-toolbar-users-report-trigger")),
    ].filter(Boolean);
    const reportOverlay = document.getElementById("toolbar-users-report-overlay");
    const reportClose = document.getElementById("toolbar-users-report-close");
    const reportCancel = document.getElementById("toolbar-users-report-cancel");
    const reportForm = document.getElementById("toolbar-users-report-form");
    const reportScope = document.getElementById("toolbar-users-report-scope");
    const individualSection = document.getElementById("toolbar-users-individual-section");
    const generalSection = document.getElementById("toolbar-users-general-section");
    const userIdInput = document.getElementById("toolbar-users-id-input");
    const userIdHint = document.getElementById("toolbar-users-id-hint");
    const departamentoSelect = document.getElementById("toolbar-users-departamento");
    const municipioSelect = document.getElementById("toolbar-users-municipio");
    const deptDataNode = document.getElementById("toolbar-users-departamentos-data");
    const searchInput = document.getElementById("toolbar-users-search-input");

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

    function closeMobileMenu() {
        document.querySelectorAll(".toolbar-admin-mobile-menu details[open]").forEach(function (detailsNode) {
            detailsNode.open = false;
        });
    }

    function resolveUserById(userId) {
        const button = document.querySelector('.users-table__button--message[data-user-id="' + userId + '"]');
        if (!button) {
            return null;
        }
        return {
            id: userId,
            name: (button.getAttribute("data-user-name") || "").trim(),
            document: (button.getAttribute("data-user-document") || "").trim(),
        };
    }

    function updateScopeUI() {
        if (!reportScope || !individualSection || !generalSection) {
            return;
        }
        const isIndividual = reportScope.value === "individual";
        individualSection.hidden = !isIndividual;
        generalSection.hidden = isIndividual;

        if (userIdInput) {
            userIdInput.disabled = !isIndividual;
            if (!isIndividual) {
                userIdInput.value = "";
            }
        }

        updateUserSuggestion();
    }

    function updateUserSuggestion() {
        if (!userIdInput || !userIdHint) {
            return;
        }
        const raw = (userIdInput.value || "").trim();
        if (!raw) {
            userIdHint.textContent = "Escribe un ID y verás la sugerencia del usuario.";
            return;
        }
        const user = resolveUserById(raw);
        if (user && user.name) {
            const docLabel = user.document ? " | Documento: " + user.document : "";
            userIdHint.textContent = "Sugerencia: ID " + user.id + " | " + user.name + docLabel;
        } else {
            userIdHint.textContent = "No se encontró ese ID en la tabla actual. Igualmente puedes generarlo si existe en base de datos.";
        }
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

    reportTriggers.forEach(function (triggerNode) {
        triggerNode.addEventListener("click", function (event) {
            event.preventDefault();
            reportOverlay.classList.add("is-open");
            reportOverlay.setAttribute("aria-hidden", "false");
            updateScopeUI();
            updateUserSuggestion();
        });
    });

    const sendMessageDesktop = document.getElementById("toolbar-enviar-mensaje");
    const sendMessageMobile = document.getElementById("toolbar-enviar-mensaje-mobile");
    if (sendMessageDesktop && sendMessageMobile) {
        sendMessageMobile.addEventListener("click", function (event) {
            event.preventDefault();
            sendMessageDesktop.click();
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
            if (userIdInput && !isIndividual) {
                userIdInput.value = "";
            }
        });
    }

    if (reportScope) {
        reportScope.addEventListener("change", updateScopeUI);
    }
    if (userIdInput) {
        userIdInput.addEventListener("input", updateUserSuggestion);
        userIdInput.addEventListener("change", updateUserSuggestion);
    }
    if (departamentoSelect) {
        departamentoSelect.addEventListener("change", updateMunicipiosOptions);
    }

    setupTableSearch(searchInput, ".products-table__body tr");

    updateScopeUI();
    updateUserSuggestion();
    updateMunicipiosOptions();

    window.addEventListener("click", function (event) {
        if (!event.target.closest(".toolbar-main__profile-dropdown")) {
            closeProfileMenu();
        }
        if (!event.target.closest(".toolbar-admin-mobile-menu")) {
            closeMobileMenu();
        }
        if (reportOverlay && event.target === reportOverlay) {
            closeReportModal();
        }
    });

    window.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeProfileMenu();
            closeMobileMenu();
            closeReportModal();
        }
    });
});