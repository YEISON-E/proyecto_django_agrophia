document.addEventListener("DOMContentLoaded", function () {
  const departamentosNode = document.getElementById("departamentos-municipios-data");
  if (!departamentosNode) {
    return;
  }

  const departamentosMunicipios = JSON.parse(departamentosNode.textContent || "{}");

  function bindDepartamentoMunicipio(departamentoId, municipioId) {
    const departamentoSelect = document.getElementById(departamentoId);
    const municipioSelect = document.getElementById(municipioId);
    if (!departamentoSelect || !municipioSelect) {
      return;
    }

    const poblarMunicipios = function () {
      const dep = departamentoSelect.value;
      const municipioActualRaw = municipioSelect.getAttribute("data-selected") || municipioSelect.value;
      const municipioActual = (municipioActualRaw || "").trim();
      municipioSelect.innerHTML = '<option value="">Selecciona un municipio</option>';
      if (!departamentosMunicipios[dep]) {
        if (municipioActual) {
          const optActual = document.createElement("option");
          optActual.value = municipioActual;
          optActual.textContent = municipioActual;
          optActual.selected = true;
          municipioSelect.appendChild(optActual);
          municipioSelect.setAttribute("data-selected", municipioActual);
        }
        return;
      }

      let encontroMunicipio = false;

      const normalizar = function (valor) {
        return (valor || "").trim().toLowerCase();
      };

      departamentosMunicipios[dep].forEach(function (mun) {
        const munTexto = (mun || "").trim();
        const opt = document.createElement("option");
        opt.value = munTexto;
        opt.textContent = munTexto;
        if (municipioActual && normalizar(municipioActual) === normalizar(munTexto)) {
          opt.selected = true;
          encontroMunicipio = true;
        }
        municipioSelect.appendChild(opt);
      });

      // Si el municipio actual no viene dentro de la lista del departamento,
      // lo mantenemos para no perder el valor guardado al editar.
      if (municipioActual && !encontroMunicipio) {
        const optActual = document.createElement("option");
        optActual.value = municipioActual;
        optActual.textContent = municipioActual;
        optActual.selected = true;
        municipioSelect.appendChild(optActual);
      }

      municipioSelect.setAttribute("data-selected", municipioSelect.value || municipioActual || "");
    };

    departamentoSelect.addEventListener("change", function () {
      municipioSelect.setAttribute("data-selected", "");
      poblarMunicipios();
    });

    poblarMunicipios();
  }

  bindDepartamentoMunicipio("departamento-select", "municipio-select");
  bindDepartamentoMunicipio("owner-departamento-select", "owner-municipio-select");

  const municipioSelect = document.getElementById("municipio-select");
  const ownerMunicipioSelect = document.getElementById("owner-municipio-select");

  const validarMunicipioSelect = function (selectElement) {
    if (!selectElement) {
      return true;
    }

    if (!selectElement.value) {
      selectElement.setCustomValidity("Debes seleccionar un municipio de la lista.");
      return false;
    }

    selectElement.setCustomValidity("");
    return true;
  };

  municipioSelect?.addEventListener("change", function () {
    validarMunicipioSelect(municipioSelect);
  });

  ownerMunicipioSelect?.addEventListener("change", function () {
    validarMunicipioSelect(ownerMunicipioSelect);
  });

  const puntoFisicoSelect = document.getElementById("punto-fisico-select");
  const horarioRow = document.getElementById("horario-row");
  const direccionRow = document.getElementById("direccion-row");
  const horarioInput = document.getElementById("horario-input");
  const direccionInput = document.getElementById("direccion-input");
  const form = puntoFisicoSelect ? puntoFisicoSelect.closest("form") : document.querySelector(".user-detail-main form");
  const confirmModal = document.getElementById("shop-confirm-modal");
  const confirmAcceptBtn = document.getElementById("shop-confirm-accept");
  const confirmCancelBtn = document.getElementById("shop-confirm-cancel");
  const confirmCloseBackdrop = confirmModal?.querySelector("[data-confirm-close]");
  let envioConfirmado = false;

  const abrirConfirmacion = function () {
    if (!confirmModal) {
      return;
    }
    confirmModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("user-lightbox-open");
    confirmAcceptBtn?.focus();
  };

  const cerrarConfirmacion = function () {
    if (!confirmModal) {
      return;
    }
    confirmModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("user-lightbox-open");
  };

  confirmCancelBtn?.addEventListener("click", function () {
    cerrarConfirmacion();
  });

  confirmCloseBackdrop?.addEventListener("click", function () {
    cerrarConfirmacion();
  });

  confirmAcceptBtn?.addEventListener("click", function () {
    cerrarConfirmacion();
    envioConfirmado = true;
    form?.requestSubmit();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && confirmModal?.getAttribute("aria-hidden") === "false") {
      cerrarConfirmacion();
    }
  });

  const resolverCajaError = function (fieldName) {
    if (!form || !fieldName) {
      return null;
    }
    return form.querySelector('[data-error-for="' + fieldName + '"]');
  };

  const mostrarErrorCampo = function (fieldElement, mensaje) {
    if (!fieldElement) {
      return;
    }
    const cajaError = resolverCajaError(fieldElement.name);
    if (cajaError) {
      cajaError.textContent = mensaje || "";
    }
    fieldElement.classList.toggle("shop-edit-input-error", Boolean(mensaje));
  };

  const actualizarErrorCampo = function (fieldElement) {
    if (!fieldElement) {
      return;
    }
    if (fieldElement.checkValidity()) {
      mostrarErrorCampo(fieldElement, "");
      return;
    }
    mostrarErrorCampo(fieldElement, fieldElement.validationMessage);
  };

  const enlazarErroresNativos = function () {
    if (!form) {
      return;
    }

    const campos = form.querySelectorAll("input[name], select[name], textarea[name]");
    campos.forEach(function (campo) {
      campo.addEventListener("invalid", function () {
        actualizarErrorCampo(campo);
      });

      const eventoCambio = campo.tagName === "SELECT" ? "change" : "input";
      campo.addEventListener(eventoCambio, function () {
        actualizarErrorCampo(campo);
      });
    });
  };

  const ajustarCamposPuntoFisico = function () {
    if (!puntoFisicoSelect) {
      return;
    }

    const usaPuntoFisico = puntoFisicoSelect.value === "True";
    if (horarioRow) {
      horarioRow.style.display = usaPuntoFisico ? "" : "none";
    }
    if (direccionRow) {
      direccionRow.style.display = usaPuntoFisico ? "" : "none";
    }
    if (horarioInput) {
      horarioInput.disabled = !usaPuntoFisico;
      horarioInput.required = usaPuntoFisico;
      if (!usaPuntoFisico) {
        horarioInput.setCustomValidity("");
        mostrarErrorCampo(horarioInput, "");
        horarioInput.value = "";
      }
    }
    if (direccionInput) {
      direccionInput.disabled = !usaPuntoFisico;
      direccionInput.required = usaPuntoFisico;
      if (!usaPuntoFisico) {
        direccionInput.setCustomValidity("");
        mostrarErrorCampo(direccionInput, "");
      }
    }
  };

  const validarHorario = function () {
    if (!horarioInput || !puntoFisicoSelect || puntoFisicoSelect.value === "False") {
      horarioInput?.setCustomValidity("");
      return true;
    }

    const valorHorario = horarioInput.value.trim();
    if (!valorHorario) {
      horarioInput.setCustomValidity("");
      return true;
    }

    const match = valorHorario.match(/^((?:0?[1-9]|1[0-2]):[0-5][0-9]\s*[AaPp][Mm])\s*-\s*((?:0?[1-9]|1[0-2]):[0-5][0-9]\s*[AaPp][Mm])$/);
    if (!match) {
      horarioInput.setCustomValidity("Usa formato HH:MM AM/PM - HH:MM AM/PM.");
      return false;
    }

    const convertirAMPM = function (horaTexto) {
      const timeMatch = horaTexto.trim().match(/^(0?[1-9]|1[0-2]):([0-5][0-9])\s*([AaPp][Mm])$/);
      if (!timeMatch) {
        return null;
      }
      let horas = Number(timeMatch[1]);
      const minutos = Number(timeMatch[2]);
      const meridiano = timeMatch[3].toUpperCase();

      if (meridiano === "AM") {
        if (horas === 12) {
          horas = 0;
        }
      } else if (horas !== 12) {
        horas += 12;
      }

      return horas * 60 + minutos;
    };

    const apertura = convertirAMPM(match[1]);
    const cierre = convertirAMPM(match[2]);
    if (apertura === null || cierre === null) {
      horarioInput.setCustomValidity("Usa formato HH:MM AM/PM - HH:MM AM/PM.");
      return false;
    }

    if (cierre <= apertura) {
      horarioInput.setCustomValidity("La hora de cierre debe ser mayor que la de apertura.");
      return false;
    }

    horarioInput.setCustomValidity("");
    return true;
  };

  puntoFisicoSelect?.addEventListener("change", function () {
    ajustarCamposPuntoFisico();
    validarHorario();
  });
  horarioInput?.addEventListener("input", validarHorario);
  horarioInput?.addEventListener("blur", validarHorario);
  ajustarCamposPuntoFisico();
  enlazarErroresNativos();

  form?.addEventListener("submit", function (event) {
    if (envioConfirmado) {
      envioConfirmado = false;
      return;
    }

    const horarioValido = validarHorario();
    const municipioValido = validarMunicipioSelect(municipioSelect);
    const ownerMunicipioValido = validarMunicipioSelect(ownerMunicipioSelect);

    if (!municipioValido) {
      mostrarErrorCampo(municipioSelect, municipioSelect.validationMessage);
    } else {
      mostrarErrorCampo(municipioSelect, "");
    }

    if (!ownerMunicipioValido) {
      mostrarErrorCampo(ownerMunicipioSelect, ownerMunicipioSelect.validationMessage);
    } else {
      mostrarErrorCampo(ownerMunicipioSelect, "");
    }

    if (!horarioValido) {
      mostrarErrorCampo(horarioInput, horarioInput?.validationMessage || "Horario inválido.");
    } else {
      mostrarErrorCampo(horarioInput, "");
    }

    if (!horarioValido || !municipioValido || !ownerMunicipioValido) {
      event.preventDefault();

      if (!municipioValido) {
        municipioSelect?.reportValidity();
        return;
      }

      if (!ownerMunicipioValido) {
        ownerMunicipioSelect?.reportValidity();
        return;
      }

      horarioInput?.reportValidity();
      return;
    }

    if (form && !form.checkValidity()) {
      event.preventDefault();
      const primerInvalido = form.querySelector(":invalid");
      if (primerInvalido) {
        actualizarErrorCampo(primerInvalido);
        primerInvalido.reportValidity();
        primerInvalido.focus();
      }
      return;
    }

    event.preventDefault();
    abrirConfirmacion();
  });

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
