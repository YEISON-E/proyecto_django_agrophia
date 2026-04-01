document.addEventListener("DOMContentLoaded", function () {
  const flash = document.getElementById("flash-product-created");
  if (!flash) {
    return;
  }

  const redirectUrl = flash.dataset.redirectUrl;

  const noticeTotalDurationMs = 4000;
  const noticeFadeDurationMs = 250;

  setTimeout(function () {
    flash.classList.add("flash-product-created--hide");
  }, noticeTotalDurationMs - noticeFadeDurationMs);

  setTimeout(function () {
    if (redirectUrl) {
      window.location.href = redirectUrl;
      return;
    }
    flash.remove();
  }, noticeTotalDurationMs);
});
