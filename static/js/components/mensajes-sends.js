// Espera a que el DOM esté listo para inicializar lógica de mensajes enviados.
document.addEventListener("DOMContentLoaded", function () {
  const setChatViewportHeight = function () {
    const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    document.documentElement.style.setProperty("--chat-vh", `${Math.round(viewportHeight)}px`);
  };

  setChatViewportHeight();
  window.addEventListener("resize", setChatViewportHeight);
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", setChatViewportHeight);
    window.visualViewport.addEventListener("scroll", setChatViewportHeight);
  }

  // Busca el contenedor de conversación.
  const conversation = document.querySelector(".messages__conversation");
  // Si existe, hace scroll hasta el final para mostrar lo más reciente.
  if (conversation) {
    conversation.scrollTop = conversation.scrollHeight;
  }

  // Busca textarea de respuesta.
  const replyTextarea = document.querySelector(".messages__reply-text");
  // Si existe, activa envío con Enter.
  if (replyTextarea) {
    const keepInputVisible = function () {
      window.setTimeout(function () {
        setChatViewportHeight();
        if (conversation) {
          conversation.scrollTop = conversation.scrollHeight;
        }
      }, 80);
    };

    replyTextarea.addEventListener("focus", keepInputVisible);
    replyTextarea.addEventListener("click", keepInputVisible);

    // Escucha pulsaciones de teclado en el textarea.
    replyTextarea.addEventListener("keydown", function (event) {
      // Si no es Enter o viene con Shift, no intercepta.
      if (event.key !== "Enter" || event.shiftKey) {
        return;
      }
      // Evita salto de línea por defecto.
      event.preventDefault();
      // Busca formulario contenedor.
      const form = replyTextarea.closest("form");
      // Si existe formulario, lo envía programáticamente.
      if (form) {
        form.requestSubmit();
      }
    });
  }
});