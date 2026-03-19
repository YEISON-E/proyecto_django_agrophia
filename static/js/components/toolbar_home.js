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
    const outputFormat = document.getElementById("toolbar-home-output-format");

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

    toggleButton.addEventListener("click", function (event) {
        event.stopPropagation();
        menu.style.display = menu.style.display === "block" ? "none" : "block";
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
    if (reportForm && outputFormat) {
        reportForm.addEventListener("submit", function () {
            reportForm.target = outputFormat.value === "print" ? "_blank" : "_self";
        });
    }

    window.addEventListener("click", function (event) {
        if (!event.target.closest(".toolbar-main__profile-dropdown")) {
            menu.style.display = "none";
        }
        if (reportOverlay && event.target === reportOverlay) {
            closeReportModal();
        }
    });

    window.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeReportModal();
        }
    });
});