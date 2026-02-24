document.addEventListener("DOMContentLoaded", function () {
  const body = document.body;
  const loginUrl = body?.dataset.loginUrl;

  if (loginUrl) {
    window.history.replaceState(null, "", window.location.href);
    window.addEventListener("popstate", function () {
      window.location.href = loginUrl;
    });
  }

  document.addEventListener("click", function (event) {
    const menuDetails = document.querySelector(".nav-menu details");
    if (!menuDetails) {
      return;
    }
    if (!menuDetails.contains(event.target)) {
      menuDetails.removeAttribute("open");
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") {
      return;
    }
    const menuDetails = document.querySelector(".nav-menu details");
    if (menuDetails) {
      menuDetails.removeAttribute("open");
    }
  });
});
