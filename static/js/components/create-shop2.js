/**
 * CREATE SHOP - PASO 2
 *
 * Valida horario comercial:
 * - Hora de apertura obligatoria
 * - Hora de cierre obligatoria
 * - Hora de cierre mayor que la apertura
 */
document.addEventListener("DOMContentLoaded", function () {
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

    togglePhysicalFields();

    // Previene submit si el horario es inválido
    form.addEventListener("submit", function (event) {
        if (!validateHorario()) {
            event.preventDefault();
        }
    });
});