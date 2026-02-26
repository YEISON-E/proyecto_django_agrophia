document.addEventListener("DOMContentLoaded", function () {
  const govcoElement = document.querySelector(".govco-container__one");

  if (!govcoElement) {
    return;
  }

  if (govcoElement.innerHTML.trim().length > 0) {
    return;
  }

  fetch("/frontend/public/views/components/gov-co__one.html")
    .then(response => response.text())
    .then(data => {
      govcoElement.innerHTML = data;
    })
    .catch(error => console.log("Error cargando el gov.co 1", error));
});
