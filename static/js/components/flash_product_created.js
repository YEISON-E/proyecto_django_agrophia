// Espera a que el DOM esté completamente cargado para iniciar la lógica del aviso.
document.addEventListener("DOMContentLoaded", function () {
  // Busca el elemento visual del mensaje flash de producto creado.
  const flash = document.getElementById("flash-product-created");
  // Si no existe el elemento, no hay nada que procesar.
  if (!flash) {
    // Sale sin ejecutar temporizadores.
    return;
  }

  // Obtiene la URL de redirección opcional desde data attribute.
  const redirectUrl = flash.dataset.redirectUrl;

  // Define la duración total visible del aviso en milisegundos.
  const noticeTotalDurationMs = 4000;
  // Define cuánto dura la animación de desvanecido en milisegundos.
  const noticeFadeDurationMs = 250;

  // Programa el inicio del efecto fade justo antes de finalizar el tiempo total.
  setTimeout(function () {
    // Agrega clase CSS que activa la animación de ocultamiento.
    flash.classList.add("flash-product-created--hide");
  }, noticeTotalDurationMs - noticeFadeDurationMs);

  // Programa la acción final cuando termina el tiempo total del aviso.
  setTimeout(function () {
    // Si existe URL de redirección, navega a esa ruta.
    if (redirectUrl) {
      window.location.href = redirectUrl;
      // Sale para evitar remover el nodo después de redirigir.
      return;
    }
    // Si no hay redirección, elimina el aviso del DOM.
    flash.remove();
  }, noticeTotalDurationMs);
});
