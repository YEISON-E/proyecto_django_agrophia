// Espera a que el DOM esté cargado para inicializar el carrusel hero.
document.addEventListener("DOMContentLoaded", function () {
  // Obtiene pista deslizante del carrusel.
  const track   = document.querySelector(".hero-carousel__track");
  // Obtiene todas las diapositivas.
  const slides  = document.querySelectorAll(".hero-carousel__slide");
  // Obtiene indicadores de posición (dots).
  const dots    = document.querySelectorAll(".hero-carousel__dot");
  // Obtiene botón de navegación anterior.
  const btnPrev = document.querySelector(".hero-carousel__arrow--prev");
  // Obtiene botón de navegación siguiente.
  const btnNext = document.querySelector(".hero-carousel__arrow--next");

  // Si falta pista o no hay slides, no inicializa carrusel.
  if (!track || !slides.length) return;

  // Índice actual del slide visible.
  let current  = 0;
  // Referencia al intervalo de autoplay.
  let autoplay = null;
  // Total de diapositivas disponibles.
  const total  = slides.length;

  // Mueve el carrusel al índice solicitado.
  function goTo(index) {
    // Ajusta índice con aritmética circular.
    current = (index + total) % total;
    // Aplica transformación horizontal para mostrar slide actual.
    track.style.transform = `translateX(-${current * 100}%)`;
    // Actualiza estado activo de los indicadores.
    dots.forEach((d, i) => d.classList.toggle("hero-carousel__dot--active", i === current));
  }

  // Inicia avance automático del carrusel.
  function startAutoplay() {
    autoplay = setInterval(() => goTo(current + 1), 4500);
  }

  // Reinicia autoplay tras interacción manual.
  function resetAutoplay() {
    clearInterval(autoplay);
    startAutoplay();
  }

  // Si existe botón previo, retrocede y reinicia autoplay.
  if (btnPrev) btnPrev.addEventListener("click", () => { goTo(current - 1); resetAutoplay(); });
  // Si existe botón siguiente, avanza y reinicia autoplay.
  if (btnNext) btnNext.addEventListener("click", () => { goTo(current + 1); resetAutoplay(); });

  // Permite navegación por clic en indicadores.
  dots.forEach((dot, i) => {
    dot.addEventListener("click", () => { goTo(i); resetAutoplay(); });
  });

  // Variables para detección de swipe táctil.
  let touchStartX = 0;
  // Guarda coordenada inicial al tocar.
  track.addEventListener("touchstart", (e) => { touchStartX = e.touches[0].clientX; }, { passive: true });
  // Calcula desplazamiento final y cambia slide si supera umbral.
  track.addEventListener("touchend", (e) => {
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 40) { goTo(diff > 0 ? current + 1 : current - 1); resetAutoplay(); }
  }, { passive: true });

  // Renderiza primer slide al iniciar.
  goTo(0);
  // Inicia rotación automática.
  startAutoplay();
});
