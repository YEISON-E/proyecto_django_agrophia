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

        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
            const data = await response.json();
            return data;
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
    const adminModal = document.getElementById("admin-reactivation-modal");
    const adminModalBackdrop = document.getElementById("admin-reactivation-backdrop");
    const adminModalClose = document.getElementById("close-admin-reactivation-modal");
    const adminForm = document.getElementById("admin-reactivation-form");
    const adminTextarea = document.getElementById("admin-reactivation-text");
    const feedbackOverlay = document.getElementById("feedback-overlay");
    const feedbackMessage = document.getElementById("feedback-message");
    const feedbackClose = document.getElementById("feedback-close");

    if (forms.length && overlay && cancelButton && confirmButton) {
        let pendingForm = null;
        let pendingAdminRequestUrl = "";

        const postAdminMessage = async function (url, messageText) {
            const csrftoken = getCookie("csrftoken");
            const body = new FormData();
            body.append("message", messageText);

            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: body,
                credentials: "same-origin",
            });

            const data = await response.json();
            if (!response.ok || !data.ok) {
                throw new Error(data.message || "No se pudo enviar la solicitud.");
            }
            return data;
        };

        const showFeedback = function (messageText) {
            if (!feedbackOverlay || !feedbackMessage) {
                return;
            }

            feedbackMessage.textContent = messageText;
            feedbackOverlay.classList.remove("profile-shop-alert-overlay--closing");
            feedbackOverlay.classList.add("profile-shop-alert-overlay--open");
            feedbackOverlay.setAttribute("aria-hidden", "false");
        };

        const closeFeedback = function () {
            if (!feedbackOverlay || !feedbackOverlay.classList.contains("profile-shop-alert-overlay--open")) {
                return;
            }

            feedbackOverlay.classList.add("profile-shop-alert-overlay--closing");
            feedbackOverlay.setAttribute("aria-hidden", "true");

            window.setTimeout(function () {
                feedbackOverlay.classList.remove("profile-shop-alert-overlay--open", "profile-shop-alert-overlay--closing");
            }, 180);
        };

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

        const openAdminModal = function (requestUrl) {
            pendingAdminRequestUrl = requestUrl;
            if (adminTextarea) {
                adminTextarea.value = "";
            }
            adminModal.classList.add("seller-message-modal--open");
            adminModal.setAttribute("aria-hidden", "false");
        };

        const closeAdminModal = function () {
            pendingAdminRequestUrl = "";
            adminModal.classList.remove("seller-message-modal--open");
            adminModal.setAttribute("aria-hidden", "true");
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
                const result = await submitFormWithCsrf(pendingForm);
                if (result && result.requires_admin_message) {
                    showFeedback("Este producto fue deshabilitado por el administrador; si desea activarlo, por favor envíe un mensaje al administrador.");
                    const requestUrl = pendingForm.dataset.requestUrl || "";
                    if (requestUrl && adminModal && adminForm) {
                        closeOverlay();
                        openAdminModal(requestUrl);
                        return;
                    }
                }
            } catch (error) {
                showFeedback("No se pudo completar la acción. Recarga la página e intenta de nuevo.");
            } finally {
                confirmButton.disabled = false;
                closeOverlay();
            }
        });

        if (adminForm && adminModal && adminModalClose && adminModalBackdrop && adminTextarea) {
            adminModalClose.addEventListener("click", closeAdminModal);
            adminModalBackdrop.addEventListener("click", closeAdminModal);

            adminForm.addEventListener("submit", async function (event) {
                event.preventDefault();
                const messageText = (adminTextarea.value || "").trim();
                if (!pendingAdminRequestUrl) {
                    return;
                }

                const submitButton = adminForm.querySelector("button[type='submit']");
                if (submitButton) {
                    submitButton.disabled = true;
                }

                try {
                    const data = await postAdminMessage(pendingAdminRequestUrl, messageText);
                    showFeedback(data.message || "Tu solicitud fue enviada al administrador.");
                    closeAdminModal();
                } catch (error) {
                    showFeedback(error.message || "No se pudo enviar el mensaje al administrador.");
                } finally {
                    if (submitButton) {
                        submitButton.disabled = false;
                    }
                }
            });
        }

        if (feedbackClose) {
            feedbackClose.addEventListener("click", closeFeedback);
        }

        if (feedbackOverlay) {
            feedbackOverlay.addEventListener("click", function (event) {
                if (event.target === feedbackOverlay) {
                    closeFeedback();
                }
            });
        }

        overlay.addEventListener("click", function (event) {
            if (event.target === overlay) {
                closeOverlay();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && overlay.classList.contains("profile-shop-alert-overlay--open")) {
                closeOverlay();
            }

            if (event.key === "Escape" && adminModal && adminModal.classList.contains("seller-message-modal--open")) {
                closeAdminModal();
            }

            if (event.key === "Escape" && feedbackOverlay && feedbackOverlay.classList.contains("profile-shop-alert-overlay--open")) {
                closeFeedback();
            }
        });
    }
});