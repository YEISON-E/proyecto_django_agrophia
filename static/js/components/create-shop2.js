/**
 * CREATE SHOP - PASO 2
 *
 * Valida horario comercial:
 * - Hora de apertura obligatoria
 * - Hora de cierre obligatoria
 * - Hora de cierre mayor que la apertura
 */
document.addEventListener("DOMContentLoaded", function () {
    const STEP2_STORAGE_KEY = "agrophia.create_shop.step2";
    // Formulario de paso 2
    const form = document.getElementById("create-shop-step2-form");
    if (!form) {
        return;
    }

    const puntoFisicoSelect = document.getElementById("tiene_punto_fisico");
    const physicalFields = document.getElementById("shop-physical-fields");
    const horaAperturaInput = document.getElementById("hora_apertura");
    const horaCierreInput = document.getElementById("hora_cierre");
    const direccionInput = document.getElementById("direccion");
    const descripcionInput = form.querySelector("textarea[name='descripcion']");

    const persistStep2Fields = () => {
        try {
            const payload = {
                tiene_punto_fisico: puntoFisicoSelect?.value || "no",
                hora_apertura: horaAperturaInput?.value || "",
                hora_cierre: horaCierreInput?.value || "",
                direccion: direccionInput?.value || "",
                descripcion: descripcionInput?.value || "",
            };
            sessionStorage.setItem(STEP2_STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
            console.warn("No se pudo guardar el paso 2 de la tienda en sessionStorage.", error);
        }
    };

    const restoreStep2Fields = () => {
        try {
            const raw = sessionStorage.getItem(STEP2_STORAGE_KEY);
            if (!raw) {
                return;
            }
            const saved = JSON.parse(raw);
            if (puntoFisicoSelect && !puntoFisicoSelect.value && saved.tiene_punto_fisico) {
                puntoFisicoSelect.value = saved.tiene_punto_fisico;
            }
            if (puntoFisicoSelect && saved.tiene_punto_fisico) {
                puntoFisicoSelect.value = saved.tiene_punto_fisico;
            }
            if (horaAperturaInput && !horaAperturaInput.value && saved.hora_apertura) {
                horaAperturaInput.value = saved.hora_apertura;
            }
            if (horaCierreInput && !horaCierreInput.value && saved.hora_cierre) {
                horaCierreInput.value = saved.hora_cierre;
            }
            if (direccionInput && !direccionInput.value && saved.direccion) {
                direccionInput.value = saved.direccion;
            }
            if (descripcionInput && !descripcionInput.value && saved.descripcion) {
                descripcionInput.value = saved.descripcion;
            }
        } catch (error) {
            console.warn("No se pudo restaurar el paso 2 de la tienda desde sessionStorage.", error);
        }
    };

    const usaPuntoFisico = () => puntoFisicoSelect?.value !== "no";

    const togglePhysicalFields = () => {
        const mostrar = usaPuntoFisico();

        form.classList.toggle("create-shop-step2--grid", mostrar);
        form.classList.toggle("show-physical-fields", mostrar);

        if (physicalFields) {
            physicalFields.style.display = "";
        }

        if (horaAperturaInput) {
            horaAperturaInput.required = mostrar;
        }
        if (horaCierreInput) {
            horaCierreInput.required = mostrar;
        }
        if (direccionInput) {
            direccionInput.required = mostrar;
        }

        if (!mostrar) {
            setError("error-hora-apertura", "");
            setError("error-hora-cierre", "");
        }
    };

    // Helper para pintar errores inline
    const setError = (id, message) => {
        const el = document.getElementById(id);
        if (!el) {
            return;
        }
        if (message) {
            el.textContent = message;
            el.style.display = "block";
        } else {
            el.textContent = "";
            el.style.display = "none";
        }
    };

    // Reglas de validación para el rango horario
    const validateHorario = () => {
        if (!usaPuntoFisico()) {
            setError("error-hora-apertura", "");
            setError("error-hora-cierre", "");
            return true;
        }

        let hasErrors = false;

        const apertura = horaAperturaInput?.value || "";
        const cierre = horaCierreInput?.value || "";

        if (!apertura) {
            setError("error-hora-apertura", "La hora de apertura es obligatoria.");
            hasErrors = true;
        } else {
            setError("error-hora-apertura", "");
        }

        if (!cierre) {
            setError("error-hora-cierre", "La hora de cierre es obligatoria.");
            hasErrors = true;
        } else {
            setError("error-hora-cierre", "");
        }

        if (apertura && cierre && cierre <= apertura) {
            setError("error-hora-cierre", "La hora de cierre debe ser mayor que la de apertura.");
            hasErrors = true;
        }

        return !hasErrors;
    };

    // Validación en tiempo real al cambiar horas
    puntoFisicoSelect?.addEventListener("change", togglePhysicalFields);
    horaAperturaInput?.addEventListener("input", validateHorario);
    horaCierreInput?.addEventListener("input", validateHorario);
    [puntoFisicoSelect, horaAperturaInput, horaCierreInput, direccionInput, descripcionInput].forEach((field) => {
        field?.addEventListener("input", persistStep2Fields);
        field?.addEventListener("change", persistStep2Fields);
    });

    restoreStep2Fields();

    togglePhysicalFields();

    // Previene submit si el horario es inválido
    form.addEventListener("submit", function (event) {
        if (!validateHorario()) {
            event.preventDefault();
            return;
        }
        persistStep2Fields();
    });
});