document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("delete-message-modal");
    const confirmButton = document.getElementById("delete-modal-confirm");
    const cancelButton = document.getElementById("delete-modal-cancel");
    const closeElements = document.querySelectorAll("[data-close-delete-modal]");
    const deleteForms = document.querySelectorAll("[data-delete-message-form]");

    if (!modal || !confirmButton || !cancelButton || !deleteForms.length) {
        return;
    }

    let pendingForm = null;

    const openModal = (form) => {
        pendingForm = form;
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        confirmButton.focus();
    };

    const closeModal = () => {
        pendingForm = null;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
    };

    deleteForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            openModal(form);
        });
    });

    confirmButton.addEventListener("click", () => {
        if (pendingForm) {
            pendingForm.submit();
        }
    });

    cancelButton.addEventListener("click", closeModal);
    closeElements.forEach((element) => {
        element.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal.classList.contains("is-open")) {
            closeModal();
        }
    });
});
