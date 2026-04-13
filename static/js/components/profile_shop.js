document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("[data-disable-shop-form]");
    const overlay = document.getElementById("disable-shop-overlay");
    const cancelButton = document.querySelector("[data-disable-shop-cancel]");
    const confirmButton = document.querySelector("[data-disable-shop-confirm]");
    const descriptionTrigger = document.querySelector("[data-description-trigger]");
    const descriptionPopover = document.querySelector("[data-description-popover]");
    const descriptionCloseButton = document.querySelector("[data-description-close]");

    const openDescription = function () {
        if (!descriptionTrigger || !descriptionPopover) {
            return;
        }
        descriptionPopover.hidden = false;
        descriptionTrigger.setAttribute("aria-expanded", "true");
    };

    const closeDescription = function () {
        if (!descriptionTrigger || !descriptionPopover) {
            return;
        }
        descriptionPopover.hidden = true;
        descriptionTrigger.setAttribute("aria-expanded", "false");
    };

    if (descriptionTrigger && descriptionPopover) {
        descriptionTrigger.addEventListener("click", function () {
            if (descriptionPopover.hidden) {
                openDescription();
                return;
            }
            closeDescription();
        });

        descriptionTrigger.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                if (descriptionPopover.hidden) {
                    openDescription();
                    return;
                }
                closeDescription();
            }
        });
    }

    descriptionCloseButton?.addEventListener("click", function () {
        closeDescription();
    });

    document.addEventListener("click", function (event) {
        if (!descriptionTrigger || !descriptionPopover || descriptionPopover.hidden) {
            return;
        }

        const clickInsideTrigger = descriptionTrigger.contains(event.target);
        const clickInsidePopover = descriptionPopover.contains(event.target);
        if (!clickInsideTrigger && !clickInsidePopover) {
            closeDescription();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && descriptionTrigger && descriptionPopover && !descriptionPopover.hidden) {
            closeDescription();
        }
    });

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