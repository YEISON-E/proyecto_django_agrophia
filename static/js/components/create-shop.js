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
    // Formulario principal del paso 1
    const form = document.querySelector(".form-shop__body");
    if (!form) {
        return;
    }

    const nombreInput = document.getElementById("nombre");
    const telefonoInput = document.getElementById("telefono");
    const emailInput = document.getElementById("email");
    const departamentoSelect = document.getElementById("departamento");
    const municipioSelect = document.getElementById("municipio");

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
            el.style.display = "block";
        } else {
            el.textContent = "";
            el.style.display = "none";
        }
    };

    // Validación completa previa al submit
    const validate = () => {
        let hasErrors = false;

        const nombre = nombreInput?.value.trim() || "";
        if (!nombre) {
            setError("error-nombre", "El nombre es obligatorio.");
            hasErrors = true;
        } else {
            setError("error-nombre", "");
        }

        const telefono = telefonoInput?.value.trim() || "";
        if (!telefono) {
            setError("error-telefono", "El telefono es obligatorio.");
            hasErrors = true;
        } else if (!validarTelefono(telefono)) {
            setError("error-telefono", "El telefono debe tener 10 digitos.");
            hasErrors = true;
        } else {
            setError("error-telefono", "");
        }

        const email = emailInput?.value.trim() || "";
        if (!email) {
            setError("error-email", "El correo es obligatorio.");
            hasErrors = true;
        } else if (!validarEmail(email)) {
            setError("error-email", "Correo invalido.");
            hasErrors = true;
        } else {
            setError("error-email", "");
        }

        const departamento = departamentoSelect?.value || "";
        if (!departamento) {
            setError("error-departamento", "Selecciona un departamento.");
            hasErrors = true;
        } else {
            setError("error-departamento", "");
        }

        const municipio = municipioSelect?.value || "";
        if (!municipio) {
            setError("error-municipio", "Selecciona un municipio.");
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
                setError("error-municipio", "El municipio no coincide con el departamento.");
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
    [
        nombreInput,
        telefonoInput,
        emailInput,
        departamentoSelect,
        municipioSelect,
    ].forEach((field) => {
        field?.addEventListener("input", validate);
        field?.addEventListener("change", validate);
    });

    departamentoSelect?.addEventListener("change", function () {
        poblarMunicipios();
        validate();
    });

    // Inicializa municipios al cargar
    poblarMunicipios();

    // Bloquea envío si hay errores
    form.addEventListener("submit", function (event) {
        if (!validate()) {
            event.preventDefault();
        }
    });
});