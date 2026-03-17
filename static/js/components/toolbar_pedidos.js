document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("toolbar-orders-profile-toggle");
  const menu = document.getElementById("profile-dropdown-orders");
  const reportTrigger = document.getElementById("toolbar-orders-report-trigger");
  const reportOverlay = document.getElementById("toolbar-orders-report-overlay");
  const reportClose = document.getElementById("toolbar-orders-report-close");
  const reportCancel = document.getElementById("toolbar-orders-report-cancel");
  const reportForm = document.getElementById("toolbar-orders-report-form");
  const outputFormat = document.getElementById("toolbar-orders-output-format");

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

  toggleButton.addEventListener("click", function (event) {
    event.stopPropagation();
    menu.style.display = menu.style.display === "block" ? "none" : "block";
  });

  if (reportTrigger) {
    reportTrigger.addEventListener("click", function (event) {
      event.preventDefault();
      reportOverlay.classList.add("is-open");
      reportOverlay.setAttribute("aria-hidden", "false");
    });
  }
  if (reportClose) {
    reportClose.addEventListener("click", closeReportModal);
  }
  if (reportCancel) {
    reportCancel.addEventListener("click", closeReportModal);
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
