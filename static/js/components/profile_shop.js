document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("[data-disable-shop-form]");
    const overlay = document.getElementById("disable-shop-overlay");
    const cancelButton = document.querySelector("[data-disable-shop-cancel]");
    const confirmButton = document.querySelector("[data-disable-shop-confirm]");

    if (!form || !overlay || !cancelButton || !confirmButton) {
        return;
    }

    const openOverlay = function () {
        overlay.classList.remove("profile-shop-alert-overlay--closing");
        overlay.classList.add("profile-shop-alert-overlay--open");
        overlay.setAttribute("aria-hidden", "false");
    };

    const closeOverlay = function () {
        if (!overlay.classList.contains("profile-shop-alert-overlay--open")) {
            return;
        }

        overlay.classList.add("profile-shop-alert-overlay--closing");
        overlay.setAttribute("aria-hidden", "true");

        window.setTimeout(function () {
            overlay.classList.remove("profile-shop-alert-overlay--open", "profile-shop-alert-overlay--closing");
        }, 180);
    };

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        openOverlay();
    });

    cancelButton.addEventListener("click", function () {
        closeOverlay();
    });

    confirmButton.addEventListener("click", function () {
        form.submit();
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
});