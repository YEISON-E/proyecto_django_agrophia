document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById("toolbar-home-profile-toggle");
    const menu = document.getElementById("toolbar-home-profile-menu");
    const reportTrigger = document.getElementById("toolbar-home-report-trigger");
    const reportOverlay = document.getElementById("toolbar-home-report-overlay");
    const reportClose = document.getElementById("toolbar-home-report-close");
    const reportCancel = document.getElementById("toolbar-home-report-cancel");
    const scopeSelect = document.getElementById("toolbar-home-scope");
    const countFields = document.getElementById("toolbar-home-count-fields");
    const periodFields = document.getElementById("toolbar-home-period-fields");
    const reportForm = document.getElementById("toolbar-home-report-form");
    const searchInput = document.getElementById("toolbar-home-search-input");

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

    function toggleReportSections() {
        const scope = scopeSelect ? scopeSelect.value : "all";
        if (countFields) {
            countFields.hidden = scope !== "count";
        }
        if (periodFields) {
            periodFields.hidden = scope !== "period";
        }
    }

    function openReportModal(event) {
        event.preventDefault();
        if (!reportOverlay) {
            return;
        }
        reportOverlay.classList.add("is-open");
        reportOverlay.setAttribute("aria-hidden", "false");
        toggleReportSections();
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

    toggleButton.addEventListener("click", function (event) {
        event.stopPropagation();
        if (menu.style.display === "block") {
            closeProfileMenu();
            return;
        }
        openProfileMenu();
    });

    if (reportTrigger) {
        reportTrigger.addEventListener("click", openReportModal);
    }
    if (reportClose) {
        reportClose.addEventListener("click", closeReportModal);
    }
    if (reportCancel) {
        reportCancel.addEventListener("click", closeReportModal);
    }
    if (scopeSelect) {
        scopeSelect.addEventListener("change", toggleReportSections);
        toggleReportSections();
    }
    if (reportForm) {
        reportForm.target = "_self";
        bindExclusiveFieldSelection(reportForm);
    }

    setupTableSearch(searchInput, ".home-table__body tr");

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