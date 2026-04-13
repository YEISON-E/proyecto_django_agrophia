// Espera a que el DOM esté listo antes de inicializar comportamiento del chat.
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

  // Busca contenedor de conversación para ajustar scroll inicial.
  const conversation = document.querySelector(".messages__conversation");
  // Si existe la conversación, la desplaza al final para ver el último mensaje.
  if (conversation) {
    conversation.scrollTop = conversation.scrollHeight;
  }

  // Busca textarea de respuesta rápida.
  const replyTextarea = document.querySelector(".messages__reply-text");
  // Si existe, habilita envío con Enter.
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

    // Escucha teclado dentro del textarea.
    replyTextarea.addEventListener("keydown", function (event) {
      // Permite comportamiento normal si no es Enter o si usa Shift+Enter.
      if (event.key !== "Enter" || event.shiftKey) {
        return;
      }
      // Evita salto de línea al presionar Enter sin Shift.
      event.preventDefault();
      // Busca el formulario padre del textarea.
      const form = replyTextarea.closest("form");
      // Si hay formulario, dispara submit programático.
      if (form) {
        form.requestSubmit();
      }
    });
  }

  // Busca botón de regreso del chat.
  const backButton = document.querySelector(".messages__chat-back");
  // Si existe, registra evento de clic.
  if (backButton) {
    backButton.addEventListener("click", function () {
      // Mantiene navegación por defecto como fallback responsive.
    });
  }
});