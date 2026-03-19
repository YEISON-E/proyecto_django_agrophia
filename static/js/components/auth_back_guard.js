document.addEventListener("DOMContentLoaded", function () {
  window.addEventListener("pageshow", function (event) {
    const navEntries = performance.getEntriesByType("navigation");
    const navType = navEntries && navEntries.length ? navEntries[0].type : "";

    // If the page comes from browser back/forward cache, force reload so
    // server-side auth checks run again and protected pages cannot be reused.
    if (event.persisted || navType === "back_forward") {
      window.location.reload();
    }
  });
});
