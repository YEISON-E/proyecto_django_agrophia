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

    const horaAperturaInput = document.getElementById("hora_apertura");
    const horaCierreInput = document.getElementById("hora_cierre");

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
    horaAperturaInput?.addEventListener("input", validateHorario);
    horaCierreInput?.addEventListener("input", validateHorario);

    // Previene submit si el horario es inválido
    form.addEventListener("submit", function (event) {
        if (!validateHorario()) {
            event.preventDefault();
        }
    });
});