document.addEventListener("DOMContentLoaded", function () {
    const mainImage = document.querySelector(".product-detail__image--photo");
    const thumbs = Array.from(document.querySelectorAll(".product-detail__thumb"));

    const getCookie = function (name) {
        const cookieValue = document.cookie
            .split(";")
            .map((cookie) => cookie.trim())
            .find((cookie) => cookie.startsWith(name + "="));
        return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
    };

    const submitFormWithCsrf = async function (form) {
        const csrftoken = getCookie("csrftoken");
        const body = new FormData(form);

        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
            body: body,
            credentials: "same-origin",
        });

        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        if (!response.ok) {
            throw new Error("No se pudo procesar la solicitud.");
        }

        window.location.reload();
    };

    if (mainImage && thumbs.length) {
        const activateThumb = function (thumb) {
            thumbs.forEach((item) => item.classList.remove("product-detail__thumb--active"));
            thumb.classList.add("product-detail__thumb--active");
            mainImage.src = thumb.src;
            mainImage.alt = thumb.alt || mainImage.alt;
        };

        activateThumb(thumbs[0]);

        thumbs.forEach((thumb) => {
            thumb.addEventListener("click", function () {
                activateThumb(thumb);
            });
        });
    }

    const forms = Array.from(document.querySelectorAll("[data-product-action-form]"));
    const overlay = document.getElementById("disable-product-overlay");
    const cancelButton = document.querySelector("[data-disable-product-cancel]");
    const confirmButton = document.querySelector("[data-disable-product-confirm]");
    const confirmTitle = document.getElementById("disable-product-title");
    const confirmMessage = overlay ? overlay.querySelector("[data-confirm-message]") : null;
    const confirmButtonText = confirmButton;

    if (forms.length && overlay && cancelButton && confirmButton) {
        let pendingForm = null;

        const openOverlay = function (form) {
            pendingForm = form;
            if (confirmTitle && form.dataset.confirmTitle) {
                confirmTitle.textContent = form.dataset.confirmTitle;
            }
            if (confirmMessage && form.dataset.confirmMessage) {
                confirmMessage.textContent = form.dataset.confirmMessage;
            }
            if (confirmButtonText && form.dataset.confirmButton) {
                confirmButtonText.textContent = form.dataset.confirmButton;
            }

            overlay.classList.remove("profile-shop-alert-overlay--closing");
            overlay.classList.add("profile-shop-alert-overlay--open");
            overlay.setAttribute("aria-hidden", "false");
        };

        const closeOverlay = function () {
            if (!overlay.classList.contains("profile-shop-alert-overlay--open")) {
                pendingForm = null;
                return;
            }

            overlay.classList.add("profile-shop-alert-overlay--closing");
            overlay.setAttribute("aria-hidden", "true");

            window.setTimeout(function () {
                overlay.classList.remove("profile-shop-alert-overlay--open", "profile-shop-alert-overlay--closing");
                pendingForm = null;
            }, 180);
        };

        forms.forEach(function (form) {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                openOverlay(form);
            });
        });

        cancelButton.addEventListener("click", function () {
            closeOverlay();
        });

        confirmButton.addEventListener("click", async function () {
            if (!pendingForm) {
                return;
            }

            confirmButton.disabled = true;
            try {
                await submitFormWithCsrf(pendingForm);
            } catch (error) {
                alert("No se pudo completar la accion. Recarga la pagina e intenta de nuevo.");
            } finally {
                confirmButton.disabled = false;
                closeOverlay();
            }
        });

        overlay.addEventListener("click", function (event) {
            if (event.target === overlay) {
                closeOverlay();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && overlay.classList.contains("profile-shop-alert-overlay--open")) {
                closeOverlay();
            }
        });
    }
});