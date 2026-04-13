document.addEventListener("DOMContentLoaded", function () {
    const triggerImages = document.querySelectorAll("[data-zoom-image]");
    const lightbox = document.getElementById("user-image-lightbox");
    const lightboxImage = document.getElementById("user-image-lightbox-img");
    const closeButton = document.getElementById("user-image-lightbox-close");

    if (!triggerImages.length || !lightbox || !lightboxImage || !closeButton) {
        return;
    }

    const openLightbox = function (src, altText) {
        lightboxImage.src = src;
        lightboxImage.alt = altText || "Imagen ampliada";
        lightbox.setAttribute("aria-hidden", "false");
        document.body.classList.add("user-lightbox-open");
    };

    const closeLightbox = function () {
        lightbox.setAttribute("aria-hidden", "true");
        lightboxImage.src = "";
        document.body.classList.remove("user-lightbox-open");
    };

    triggerImages.forEach(function (img) {
        img.addEventListener("click", function () {
            openLightbox(img.src, img.alt);
        });
    });

    closeButton.addEventListener("click", closeLightbox);

    lightbox.addEventListener("click", function (event) {
        if (event.target === lightbox) {
            closeLightbox();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && lightbox.getAttribute("aria-hidden") === "false") {
            closeLightbox();
        }
    });
});
