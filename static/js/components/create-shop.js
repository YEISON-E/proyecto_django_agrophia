/**
 * CREATE SHOP - PASO 1
 *
 * Valida en cliente:
 * - Nombre de tienda
 * - Teléfono (10 dígitos)
 * - Correo electrónico
 * - Relación válida Departamento/Municipio
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

    // Formulario principal del paso 1
    const form = document.querySelector(".form-shop__body");
    if (!form) {
        return;
    }

    const flowId = form.dataset.shopFlowId || "default";
    const STEP1_STORAGE_KEY = `agrophia.create_shop.step1.${flowId}`;

    const nombreInput = document.getElementById("nombre");
    const telefonoInput = document.getElementById("telefono");
    const emailInput = document.getElementById("email");
    const departamentoSelect = document.getElementById("departamento");
    const municipioSelect = document.getElementById("municipio");
    let municipioPrevio = municipioSelect?.dataset.selectedMunicipio || "";
    const serverNombreError = document.getElementById("error-nombre")?.dataset.serverError || "";
    const touchedFields = new Set();
    let submitAttempted = false;

    const persistStep1Fields = () => {
        try {
            sessionStorage.removeItem(STEP1_STORAGE_KEY);
        } catch (error) {
            console.warn("No se pudo limpiar el paso 1 de la tienda en sessionStorage.", error);
        }
    };

    const restoreStep1Fields = () => {
        municipioPrevio = "";
    };

    // Normaliza texto para comparar municipios (manejo de tildes y espacios)
    const normalizarTexto = (valor) =>
        window.LocationUtils
            ? window.LocationUtils.normalizarTexto(valor)
            : (valor || "")
                    .normalize("NFD")
                    .replace(/\p{Diacritic}/gu, "")
                    .trim();

    // Validadores base reutilizables
    const validarEmail = (valor) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
    const validarTelefono = (valor) => /^\d{10}$/.test(valor);

    // Carga municipios según el departamento seleccionado
    const poblarMunicipios = () => {
        if (!municipioSelect) {
            return;
        }

        const departamento = departamentoSelect?.value || "";
        if (window.LocationUtils) {
            window.LocationUtils.poblarMunicipios(departamento, municipioSelect);
            if (municipioPrevio) {
                municipioSelect.value = municipioPrevio;
            }
            return;
        }

        municipioSelect.innerHTML = '<option value="">Selecciona el Municipio</option>';
    };

    // Muestra/oculta mensajes de error por campo
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

    const shouldShowError = (fieldKey) => submitAttempted || touchedFields.has(fieldKey);

    // Validación completa previa al submit
    const validate = () => {
        let hasErrors = false;

        const nombre = nombreInput?.value.trim() || "";
        if (!nombre) {
            if (shouldShowError("nombre")) {
                setError("error-nombre", "El nombre es obligatorio.");
            }
            hasErrors = true;
        } else if (nombre.length > 50) {
            if (shouldShowError("nombre")) {
                setError("error-nombre", "El nombre de la tienda no puede superar 50 caracteres.");
            }
            hasErrors = true;
        } else {
            setError("error-nombre", "");
        }

        const telefono = telefonoInput?.value.trim() || "";
        if (!telefono) {
            if (shouldShowError("telefono")) {
                setError("error-telefono", "El telefono es obligatorio.");
            }
            hasErrors = true;
        } else if (!validarTelefono(telefono)) {
            if (shouldShowError("telefono")) {
                setError("error-telefono", "El telefono debe tener 10 digitos.");
            }
            hasErrors = true;
        } else {
            setError("error-telefono", "");
        }

        const email = emailInput?.value.trim() || "";
        if (!email) {
            if (shouldShowError("email")) {
                setError("error-email", "El correo es obligatorio.");
            }
            hasErrors = true;
        } else if (!validarEmail(email)) {
            if (shouldShowError("email")) {
                setError("error-email", "Correo invalido.");
            }
            hasErrors = true;
        } else {
            setError("error-email", "");
        }

        const departamento = departamentoSelect?.value || "";
        if (!departamento) {
            if (shouldShowError("departamento")) {
                setError("error-departamento", "Selecciona un departamento.");
            }
            hasErrors = true;
        } else {
            setError("error-departamento", "");
        }

        const municipio = municipioSelect?.value || "";
        if (!municipio) {
            if (shouldShowError("municipio")) {
                setError("error-municipio", "Selecciona un municipio.");
            }
            hasErrors = true;
        } else if (departamento) {
            const lista = window.LocationUtils
                ? window.LocationUtils.municipiosPorDepartamento[departamento] || []
                : [];
            const municipioNormalizado = normalizarTexto(municipio);
            const valido = lista.some(
                (item) => normalizarTexto(item) === municipioNormalizado
            );
            if (!valido) {
                if (shouldShowError("municipio")) {
                    setError("error-municipio", "El municipio no coincide con el departamento.");
                }
                hasErrors = true;
            } else {
                setError("error-municipio", "");
            }
        } else {
            setError("error-municipio", "");
        }

        return !hasErrors;
    };

    // Validación en tiempo real
    const fieldMap = [
        { key: "nombre", el: nombreInput },
        { key: "telefono", el: telefonoInput },
        { key: "email", el: emailInput },
        { key: "departamento", el: departamentoSelect },
        { key: "municipio", el: municipioSelect },
    ];

    fieldMap.forEach(({ key, el }) => {
        el?.addEventListener("input", function () {
            touchedFields.add(key);
            validate();
        });
        el?.addEventListener("change", function () {
            touchedFields.add(key);
            validate();
        });
        el?.addEventListener("blur", function () {
            touchedFields.add(key);
            validate();
        });
        el?.addEventListener("input", persistStep1Fields);
        el?.addEventListener("change", persistStep1Fields);
    });

    departamentoSelect?.addEventListener("change", function () {
        poblarMunicipios();
        municipioPrevio = municipioSelect?.value || "";
        touchedFields.add("departamento");
        validate();
    });

    restoreStep1Fields();
    persistStep1Fields();

    // Inicializa municipios al cargar
    poblarMunicipios();

    if (municipioSelect?.dataset.selectedMunicipio) {
        municipioSelect.value = municipioSelect.dataset.selectedMunicipio;
    }

    if (serverNombreError) {
        setError("error-nombre", serverNombreError);
    }

    // Bloquea envío si hay errores
    form.addEventListener("submit", function (event) {
        submitAttempted = true;
        if (!validate()) {
            event.preventDefault();
            return;
        }
        persistStep1Fields();
    });
});