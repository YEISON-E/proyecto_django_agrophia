/**
 * CREATE SHOP - PASO 2
 *
 * Valida horario comercial:
 * - Hora de apertura obligatoria
 * - Hora de cierre obligatoria
 * - Hora de cierre mayor que la apertura
 */
document.addEventListener("DOMContentLoaded", function () {
    const backButton = document.querySelector("[data-history-back='true']");
    backButton?.addEventListener("click", function (event) {
        event.preventDefault();
        const fallbackUrl = backButton.getAttribute("data-fallback-url") || backButton.getAttribute("href") || "/";
        const referrer = document.referrer || "";
        const cameFromLogin = referrer.includes("/usuarios/login/");

        if (window.history.length > 1 && !cameFromLogin) {
            window.history.back();
            return;
        }

        window.location.href = fallbackUrl;
    });

    // Formulario de paso 2
    const form = document.getElementById("create-shop-step2-form");
    if (!form) {
        return;
    }

    const flowId = form.dataset.shopFlowId || "default";
    const STEP2_STORAGE_KEY = `agrophia.create_shop.step2.${flowId}`;
    const serverHorarioError = document.getElementById("error-hora-cierre")?.dataset.serverError || "";
    const serverDireccionError = document.getElementById("error-direccion")?.dataset.serverError || "";

    const puntoFisicoSelect = document.getElementById("tiene_punto_fisico");
    const physicalFields = document.getElementById("shop-physical-fields");
    const horaAperturaInput = document.getElementById("hora_apertura");
    const horaCierreInput = document.getElementById("hora_cierre");
    const direccionInput = document.getElementById("direccion");
    const descripcionInput = form.querySelector("textarea[name='descripcion']");
    const touchedFields = new Set();
    let submitAttempted = false;

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
            setError("error-direccion", "");
        }
    };

    const shouldShowError = (fieldKey) => submitAttempted || touchedFields.has(fieldKey);

    // Helper para pintar errores inline
    const setError = (id, message) => {
        const el = document.getElementById(id);
        if (!el) {
            return;
        }
        if (message) {
            el.textContent = message;
            el.classList.add("is-visible");
            el.style.display = "flex";
        } else {
            el.textContent = "";
            el.classList.remove("is-visible");
            el.style.display = "none";
        }
    };

    // Reglas de validación para el rango horario
    const validateHorario = () => {
        if (!usaPuntoFisico()) {
            setError("error-hora-apertura", "");
            setError("error-hora-cierre", "");
            setError("error-direccion", "");
            return true;
        }

        let hasErrors = false;

        const apertura = horaAperturaInput?.value || "";
        const cierre = horaCierreInput?.value || "";
        const direccion = direccionInput?.value.trim() || "";

        if (!apertura) {
            if (shouldShowError("hora_apertura")) {
                setError("error-hora-apertura", "La hora de apertura es obligatoria.");
            }
            hasErrors = true;
        } else {
            setError("error-hora-apertura", "");
        }

        if (!cierre) {
            if (shouldShowError("hora_cierre")) {
                setError("error-hora-cierre", "La hora de cierre es obligatoria.");
            }
            hasErrors = true;
        } else {
            setError("error-hora-cierre", "");
        }

        if (apertura && cierre && cierre <= apertura) {
            if (shouldShowError("hora_cierre")) {
                setError("error-hora-cierre", "La hora de cierre debe ser mayor que la de apertura.");
            }
            hasErrors = true;
        }

        if (!direccion) {
            if (shouldShowError("direccion")) {
                setError("error-direccion", "La direccion es obligatoria si tienes punto fisico.");
            }
            hasErrors = true;
        } else {
            setError("error-direccion", "");
        }

        return !hasErrors;
    };

    // Validación en tiempo real al cambiar horas
    puntoFisicoSelect?.addEventListener("change", function () {
        touchedFields.add("tiene_punto_fisico");
        togglePhysicalFields();
        validateHorario();
    });
    horaAperturaInput?.addEventListener("input", function () {
        touchedFields.add("hora_apertura");
        validateHorario();
    });
    horaAperturaInput?.addEventListener("blur", function () {
        touchedFields.add("hora_apertura");
        validateHorario();
    });
    horaCierreInput?.addEventListener("input", function () {
        touchedFields.add("hora_cierre");
        validateHorario();
    });
    horaCierreInput?.addEventListener("blur", function () {
        touchedFields.add("hora_cierre");
        validateHorario();
    });
    direccionInput?.addEventListener("input", function () {
        touchedFields.add("direccion");
        validateHorario();
    });
    direccionInput?.addEventListener("blur", function () {
        touchedFields.add("direccion");
        validateHorario();
    });
    [puntoFisicoSelect, horaAperturaInput, horaCierreInput, direccionInput, descripcionInput].forEach((field) => {
        field?.addEventListener("input", persistStep2Fields);
        field?.addEventListener("change", persistStep2Fields);
    });

    restoreStep2Fields();

    togglePhysicalFields();

    if (serverHorarioError) {
        setError("error-hora-cierre", serverHorarioError);
    }
    if (serverDireccionError) {
        setError("error-direccion", serverDireccionError);
    }

    // Previene submit si el horario es inválido
    form.addEventListener("submit", function (event) {
        submitAttempted = true;
        if (!validateHorario()) {
            event.preventDefault();
            return;
        }
        persistStep2Fields();
    });
});