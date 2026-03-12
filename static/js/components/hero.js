document.addEventListener("DOMContentLoaded", function () {
  const track   = document.querySelector(".hero-carousel__track");
  const slides  = document.querySelectorAll(".hero-carousel__slide");
  const dots    = document.querySelectorAll(".hero-carousel__dot");
  const btnPrev = document.querySelector(".hero-carousel__arrow--prev");
  const btnNext = document.querySelector(".hero-carousel__arrow--next");

  if (!track || !slides.length) return;

  let current  = 0;
  let autoplay = null;
  const total  = slides.length;

  function goTo(index) {
    current = (index + total) % total;
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle("hero-carousel__dot--active", i === current));
  }

  function startAutoplay() {
    autoplay = setInterval(() => goTo(current + 1), 4500);
  }

  function resetAutoplay() {
    clearInterval(autoplay);
    startAutoplay();
  }

  if (btnPrev) btnPrev.addEventListener("click", () => { goTo(current - 1); resetAutoplay(); });
  if (btnNext) btnNext.addEventListener("click", () => { goTo(current + 1); resetAutoplay(); });

  dots.forEach((dot, i) => {
    dot.addEventListener("click", () => { goTo(i); resetAutoplay(); });
  });

  // Swipe táctil
  let touchStartX = 0;
  track.addEventListener("touchstart", (e) => { touchStartX = e.touches[0].clientX; }, { passive: true });
  track.addEventListener("touchend", (e) => {
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 40) { goTo(diff > 0 ? current + 1 : current - 1); resetAutoplay(); }
  }, { passive: true });

  goTo(0);
  startAutoplay();
});
