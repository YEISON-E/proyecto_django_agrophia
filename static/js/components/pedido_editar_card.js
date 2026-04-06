document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("order-edit-form");
  const modal = document.getElementById("order-confirm-modal");
  const btnAccept = document.getElementById("order-confirm-accept");
  const btnCancel = document.getElementById("order-confirm-cancel");
  const backdrop = modal ? modal.querySelector("[data-order-confirm-close]") : null;

  if (!form || !modal || !btnAccept || !btnCancel) {
    return;
  }

  let envioConfirmado = false;

  const abrir = function () {
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("user-lightbox-open");
    btnAccept.focus();
  };

  const cerrar = function () {
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("user-lightbox-open");
  };

  form.addEventListener("submit", function (event) {
    if (envioConfirmado) {
      envioConfirmado = false;
      return;
    }

    event.preventDefault();
    abrir();
  });

  btnAccept.addEventListener("click", function () {
    cerrar();
    envioConfirmado = true;
    form.requestSubmit();
  });

  btnCancel.addEventListener("click", cerrar);
  backdrop?.addEventListener("click", cerrar);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && modal.getAttribute("aria-hidden") === "false") {
      cerrar();
    }
  });
});
