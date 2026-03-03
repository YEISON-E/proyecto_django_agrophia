document.addEventListener("DOMContentLoaded", function () {
  initializeProductImageGallery();

  // === Función para inicializar el cambio de imágenes ===
  function initializeProductImageGallery() {
    const mainImage = document.getElementById("main-image");
    const thumbnails = document.querySelectorAll(".product-view__thumbnail");

    if (!mainImage || thumbnails.length === 0) return;

    thumbnails.forEach((thumbnail) => {
      thumbnail.addEventListener("click", () => {
        // Cambiar la imagen principal
        mainImage.src = thumbnail.src;

        // Quitar borde activo de todas las miniaturas
        thumbnails.forEach((t) => t.classList.remove("product-view__thumbnail--active"));

        // Agregar borde activo a la seleccionada
        thumbnail.classList.add("product-view__thumbnail--active");

        // Pequeño efecto de transición (fade)
        mainImage.classList.add("fade");
        setTimeout(() => mainImage.classList.remove("fade"), 300);
      });
    });
  }
});
