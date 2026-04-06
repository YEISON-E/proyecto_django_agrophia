document.addEventListener("DOMContentLoaded", function () {
  const departamentosNode = document.getElementById("departamentos-municipios-data");
  const usuariosNode = document.getElementById("usuarios-disponibles-data");

  if (!departamentosNode || !usuariosNode) {
    return;
  }

  const departamentosMunicipios = JSON.parse(departamentosNode.textContent || "{}");
  const usuariosDisponibles = JSON.parse(usuariosNode.textContent || "[]");
  const usuariosPorId = Object.fromEntries(
    usuariosDisponibles.map(function (usuario) {
      return [String(usuario.id_usuario), usuario];
    })
  );

  const ownerSelect = document.getElementById("owner-select");
  const departamentoSelect = document.getElementById("departamento-select");
  const municipioSelect = document.getElementById("municipio-select");
  const puntoFisicoSelect = document.getElementById("punto-fisico-select");
  const telefonoInput = document.getElementById("telefono-input");
  const emailInput = document.getElementById("email-input");
  const direccionInput = document.getElementById("direccion-input");
  const direccionLabel = document.getElementById("direccion-label");
  const direccionField = document.getElementById("direccion-field");
  const horarioInput = document.getElementById("horario-input");
  const horarioLabel = document.getElementById("horario-label");
  const horarioField = document.getElementById("horario-field");
  const form = ownerSelect ? ownerSelect.closest("form") : null;
  const successNode = document.querySelector(".editar-tienda-success[data-redirect-url]");

  if (!ownerSelect || !departamentoSelect || !municipioSelect || !telefonoInput || !emailInput || !direccionInput) {
    return;
  }

  const municipioSeleccionado = municipioSelect.dataset.selectedMunicipio || "";

  function renderMunicipios(departamento, municipioActual) {
    municipioSelect.innerHTML = '<option value="">Selecciona un municipio</option>';
    if (!departamentosMunicipios[departamento]) {
      return;
    }

    departamentosMunicipios[departamento].forEach(function (mun) {
      const opt = document.createElement("option");
      opt.value = mun;
      opt.textContent = mun;
      if (mun === municipioActual) {
        opt.selected = true;
      }
      municipioSelect.appendChild(opt);
    });
  }

  function autocompletarDesdeUsuario() {
    const usuario = usuariosPorId[ownerSelect.value];
    if (!usuario) {
      return;
    }

    if (!telefonoInput.value.trim()) {
      telefonoInput.value = usuario.telefono || "";
    }
    if (!emailInput.value.trim()) {
      emailInput.value = usuario.correo_electronico || "";
    }
    if (!departamentoSelect.value.trim()) {
      departamentoSelect.value = usuario.departamento || "";
      renderMunicipios(departamentoSelect.value, usuario.municipio || "");
    } else if (!municipioSelect.value.trim() && usuario.departamento === departamentoSelect.value) {
      renderMunicipios(departamentoSelect.value, usuario.municipio || "");
    }
    if (!direccionInput.value.trim()) {
      direccionInput.value = usuario.direccion_completa || "";
    }
  }

  departamentoSelect.addEventListener("change", function () {
    renderMunicipios(departamentoSelect.value, "");
  });

  ownerSelect.addEventListener("change", autocompletarDesdeUsuario);

  if (departamentoSelect.value) {
    renderMunicipios(departamentoSelect.value, municipioSeleccionado);
  }

  if (ownerSelect.value) {
    autocompletarDesdeUsuario();
  }

  const ajustarCamposPuntoFisico = function () {
    const usaPuntoFisico = puntoFisicoSelect?.value === "True";

    if (direccionLabel) {
      direccionLabel.hidden = !usaPuntoFisico;
      direccionLabel.style.display = usaPuntoFisico ? "inline-block" : "none";
    }
    if (direccionField) {
      direccionField.hidden = !usaPuntoFisico;
      direccionField.style.display = usaPuntoFisico ? "block" : "none";
    }
    if (horarioLabel) {
      horarioLabel.hidden = !usaPuntoFisico;
      horarioLabel.style.display = usaPuntoFisico ? "inline-block" : "none";
    }
    if (horarioField) {
      horarioField.hidden = !usaPuntoFisico;
      horarioField.style.display = usaPuntoFisico ? "block" : "none";
    }

    if (direccionInput) {
      direccionInput.required = usaPuntoFisico;
      if (!usaPuntoFisico) {
        direccionInput.setCustomValidity("");
      }
    }
    if (horarioInput) {
      horarioInput.required = usaPuntoFisico;
      if (!usaPuntoFisico) {
        horarioInput.setCustomValidity("");
      }
    }
  };

  const validarHorario = function () {
    if (!horarioInput) {
      return true;
    }

    if (puntoFisicoSelect && puntoFisicoSelect.value === "False") {
      horarioInput.setCustomValidity("");
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

  horarioInput?.addEventListener("input", validarHorario);
  horarioInput?.addEventListener("blur", validarHorario);
  puntoFisicoSelect?.addEventListener("change", function () {
    ajustarCamposPuntoFisico();
    validarHorario();
  });

  ajustarCamposPuntoFisico();

  form?.addEventListener("submit", function (event) {
    if (!validarHorario()) {
      event.preventDefault();
      horarioInput?.reportValidity();
    }
  });

  if (successNode) {
    const redirectUrl = successNode.dataset.redirectUrl;
    if (redirectUrl) {
      setTimeout(function () {
        window.location.href = redirectUrl;
      }, 1200);
    }
  }
});
