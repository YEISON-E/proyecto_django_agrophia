document.addEventListener("DOMContentLoaded", function () {
  const backLink = document.querySelector('[data-history-back="true"]');
  if (!backLink) {
    return;
  }

  backLink.addEventListener("click", function (event) {
    event.preventDefault();
    const fallbackUrl = backLink.getAttribute("data-fallback-url") || backLink.getAttribute("href") || "/";

    if (window.history.length > 1) {
      window.history.back();
      return;
    }

    window.location.href = fallbackUrl;
  });
});
