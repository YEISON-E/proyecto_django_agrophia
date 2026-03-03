document.addEventListener("DOMContentLoaded", function () {
  const flash = document.getElementById("flash-product-created");
  if (!flash) {
    return;
  }

  const redirectUrl = flash.dataset.redirectUrl;

  setTimeout(function () {
    flash.classList.add("flash-product-created--hide");
  }, 1200);

  setTimeout(function () {
    if (redirectUrl) {
      window.location.href = redirectUrl;
      return;
    }
    flash.remove();
  }, 1500);
});
