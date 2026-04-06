/**
 * CREATE SHOP - PASO 1
 *
 * Valida en cliente:
 * - Nombre de tienda
 * - Teléfono (10 dígitos)
 * - Correo electrónico
 * - Relación válida Departamento/Municipio
 */
// Espera a que el DOM esté listo antes de buscar elementos o registrar eventos.
document.addEventListener("DOMContentLoaded", function () {
    // Busca el botón que vuelve a la vista anterior usando un atributo de datos.
    const backButton = document.querySelector("[data-history-back='true']");
    // Si existe el botón de volver, registra su comportamiento personalizado.
    backButton?.addEventListener("click", function (event) {
        // Evita la navegación inmediata del enlace para controlar la lógica manualmente.
        event.preventDefault();
        // Define URL de respaldo: prioriza data-fallback-url, luego href, y por último la raíz.
        const fallbackUrl = backButton.getAttribute("data-fallback-url") || backButton.getAttribute("href") || "/";
        // Obtiene la URL previa del navegador para decidir el tipo de retroceso.
        const referrer = document.referrer || "";
        // Determina si la navegación previa viene de login para evitar volver allí.
        const cameFromLogin = referrer.includes("/usuarios/login/");

        // Si hay historial y no viene de login, usa historial para volver.
        if (window.history.length > 1 && !cameFromLogin) {
            // Retrocede una página en el historial.
            window.history.back();
            // Finaliza para no ejecutar redirección por URL.
            return;
        }

        // Si no puede volver de forma segura, redirige a la URL de respaldo.
        window.location.href = fallbackUrl;
    });

    // Formulario principal del paso 1
    const form = document.querySelector(".form-shop__body");
    // Si no existe el formulario, no hay nada que inicializar.
    if (!form) {
        // Termina la ejecución tempranamente.
        return;
    }

    // Recupera un identificador de flujo para aislar datos entre distintas sesiones/formularios.
    const flowId = form.dataset.shopFlowId || "default";
    // Construye la clave usada para persistencia temporal del paso 1.
    const STEP1_STORAGE_KEY = `agrophia.create_shop.step1.${flowId}`;

    // Referencia al input de nombre de la tienda.
    const nombreInput = document.getElementById("nombre");
    // Referencia al input de teléfono.
    const telefonoInput = document.getElementById("telefono");
    // Referencia al input de correo electrónico.
    const emailInput = document.getElementById("email");
    // Referencia al select de departamento.
    const departamentoSelect = document.getElementById("departamento");
    // Referencia al select de municipio.
    const municipioSelect = document.getElementById("municipio");
    // Mantiene el municipio previo para re-aplicarlo al recargar la lista.
    let municipioPrevio = municipioSelect?.dataset.selectedMunicipio || "";
    // Recupera error del servidor para nombre, si existe.
    const serverNombreError = document.getElementById("error-nombre")?.dataset.serverError || "";
    // Recupera error del servidor para teléfono, si existe.
    const serverTelefonoError = document.getElementById("error-telefono")?.dataset.serverError || "";
    // Recupera error del servidor para email, si existe.
    const serverEmailError = document.getElementById("error-email")?.dataset.serverError || "";
    // Recupera error del servidor para departamento, si existe.
    const serverDepartamentoError = document.getElementById("error-departamento")?.dataset.serverError || "";
    // Recupera error del servidor para municipio, si existe.
    const serverMunicipioError = document.getElementById("error-municipio")?.dataset.serverError || "";
    // Lleva registro de campos que el usuario ya tocó.
    const touchedFields = new Set();
    // Bandera que indica si ya intentaron enviar el formulario.
    let submitAttempted = false;

    // Limpia la persistencia temporal del paso 1 en sessionStorage.
    const persistStep1Fields = () => {
        // Intenta limpiar la clave del paso 1 para evitar residuos entre intentos.
        try {
            // Elimina cualquier valor guardado del paso 1.
            sessionStorage.removeItem(STEP1_STORAGE_KEY);
        } catch (error) {
            // Informa en consola si el navegador bloquea storage.
            console.warn("No se pudo limpiar el paso 1 de la tienda en sessionStorage.", error);
        }
    };

    // Restaura estado mínimo del paso 1 al inicializar.
    const restoreStep1Fields = () => {
        // Reinicia el municipio previo para evitar arrastres incorrectos.
        municipioPrevio = "";
    };

    // Normaliza texto para comparar municipios (manejo de tildes y espacios)
    // Define función que quita diferencias de acentos/espacios para comparaciones robustas.
    const normalizarTexto = (valor) =>
        // Si existe utilitario global de ubicaciones, reutiliza su normalización.
        window.LocationUtils
            ? window.LocationUtils.normalizarTexto(valor)
            // Si no existe utilitario, aplica una normalización local equivalente.
            : (valor || "")
                    // Descompone caracteres acentuados en base + diacrítico.
                    .normalize("NFD")
                    // Elimina marcas diacríticas usando regex Unicode.
                    .replace(/\p{Diacritic}/gu, "")
                    // Quita espacios al inicio y al final.
                    .trim();

    // Validadores base reutilizables
    // Valida formato básico de correo electrónico.
    const validarEmail = (valor) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
    // Valida teléfono exactamente de 10 dígitos numéricos.
    const validarTelefono = (valor) => /^\d{10}$/.test(valor);

    // Carga municipios según el departamento seleccionado
    // Rellena el select de municipios de acuerdo al departamento actual.
    const poblarMunicipios = () => {
        // Si no existe el select de municipio, no se puede poblar.
        if (!municipioSelect) {
            // Sale sin hacer más trabajo.
            return;
        }

        // Toma el departamento elegido o cadena vacía si no hay selección.
        const departamento = departamentoSelect?.value || "";
        // Si existe utilitario global, delega el poblamiento completo.
        if (window.LocationUtils) {
            // Rellena opciones de municipio según departamento.
            window.LocationUtils.poblarMunicipios(departamento, municipioSelect);
            // Si hay municipio previo, intenta restaurarlo tras poblar opciones.
            if (municipioPrevio) {
                // Reasigna el valor previo al select.
                municipioSelect.value = municipioPrevio;
            }
            // Finaliza porque ya se hizo el poblamiento con utilitario.
            return;
        }

        // Fallback simple cuando no hay utilitario de ubicaciones.
        municipioSelect.innerHTML = '<option value="">Selecciona el Municipio</option>';
    };

    // Muestra/oculta mensajes de error por campo
    // Centraliza la renderización de mensajes de error por id de contenedor.
    const setError = (id, message) => {
        // Obtiene el nodo donde se mostrará el error.
        const el = document.getElementById(id);
        // Si el nodo no existe, no hay nada que pintar.
        if (!el) {
            // Corta ejecución para evitar errores.
            return;
        }
        // Si hay mensaje, muestra el bloque de error.
        if (message) {
            // Inserta el texto del error.
            el.textContent = message;
            // Activa clase visual de estado visible.
            el.classList.add("is-visible");
            // Fuerza display en flex para respetar estilo de diseño.
            el.style.display = "flex";
        } else {
            // Limpia el contenido cuando no hay error.
            el.textContent = "";
            // Quita clase visual de error visible.
            el.classList.remove("is-visible");
            // Oculta completamente el contenedor de error.
            el.style.display = "none";
        }
    };

    // Determina si un campo ya debe mostrar errores al usuario.
    const shouldShowError = (fieldKey) => submitAttempted || touchedFields.has(fieldKey);

    // Validación completa previa al submit
    // Ejecuta todas las reglas y devuelve true si el formulario es válido.
    const validate = () => {
        // Bandera acumuladora de errores.
        let hasErrors = false;

        // Lee y limpia el valor de nombre.
        const nombre = nombreInput?.value.trim() || "";
        // Regla: nombre obligatorio.
        if (!nombre) {
            // Muestra mensaje solo si corresponde por interacción o submit.
            if (shouldShowError("nombre")) {
                // Presenta mensaje de requerido para nombre.
                setError("error-nombre", "El nombre es obligatorio.");
            }
            // Marca que existe al menos un error.
            hasErrors = true;
        // Regla: longitud máxima de 50 caracteres.
        } else if (nombre.length > 50) {
            // Muestra mensaje de longitud excedida si corresponde.
            if (shouldShowError("nombre")) {
                // Presenta mensaje de longitud inválida.
                setError("error-nombre", "El nombre de la tienda no puede superar 50 caracteres.");
            }
            // Marca error de validación.
            hasErrors = true;
        } else {
            // Si es válido, limpia error de nombre.
            setError("error-nombre", "");
        }

        // Lee y limpia el valor de teléfono.
        const telefono = telefonoInput?.value.trim() || "";
        // Regla: teléfono obligatorio.
        if (!telefono) {
            // Muestra mensaje solo cuando se deba visualizar.
            if (shouldShowError("telefono")) {
                // Informa que el teléfono es requerido.
                setError("error-telefono", "El telefono es obligatorio.");
            }
            // Acumula error.
            hasErrors = true;
        // Regla: teléfono con exactamente 10 dígitos.
        } else if (!validarTelefono(telefono)) {
            // Muestra error de formato cuando corresponda.
            if (shouldShowError("telefono")) {
                // Informa formato esperado para teléfono.
                setError("error-telefono", "El telefono debe tener 10 digitos.");
            }
            // Acumula error.
            hasErrors = true;
        } else {
            // Si es válido, limpia error de teléfono.
            setError("error-telefono", "");
        }

        // Lee y limpia el valor de correo.
        const email = emailInput?.value.trim() || "";
        // Regla: correo obligatorio.
        if (!email) {
            // Muestra mensaje de requerido cuando corresponda.
            if (shouldShowError("email")) {
                // Informa obligatoriedad de correo.
                setError("error-email", "El correo es obligatorio.");
            }
            // Acumula error.
            hasErrors = true;
        // Regla: correo debe cumplir formato básico.
        } else if (!validarEmail(email)) {
            // Muestra error de formato si corresponde.
            if (shouldShowError("email")) {
                // Informa que el correo no es válido.
                setError("error-email", "Correo invalido.");
            }
            // Acumula error.
            hasErrors = true;
        } else {
            // Si es válido, limpia error de email.
            setError("error-email", "");
        }

        // Obtiene departamento seleccionado.
        const departamento = departamentoSelect?.value || "";
        // Regla: departamento obligatorio.
        if (!departamento) {
            // Muestra mensaje de requerido cuando aplique.
            if (shouldShowError("departamento")) {
                // Informa que debe seleccionar departamento.
                setError("error-departamento", "Selecciona un departamento.");
            }
            // Acumula error.
            hasErrors = true;
        } else {
            // Si es válido, limpia error de departamento.
            setError("error-departamento", "");
        }

        // Obtiene municipio seleccionado.
        const municipio = municipioSelect?.value || "";
        // Regla: municipio obligatorio.
        if (!municipio) {
            // Muestra mensaje de requerido cuando corresponda.
            if (shouldShowError("municipio")) {
                // Informa que debe seleccionar municipio.
                setError("error-municipio", "Selecciona un municipio.");
            }
            // Acumula error.
            hasErrors = true;
        // Si hay departamento, valida coherencia municipio-departamento.
        } else if (departamento) {
            // Obtiene lista de municipios permitidos para el departamento.
            const lista = window.LocationUtils
                ? window.LocationUtils.municipiosPorDepartamento[departamento] || []
                : [];
            // Normaliza municipio elegido para comparación segura.
            const municipioNormalizado = normalizarTexto(municipio);
            // Verifica si el municipio elegido existe en la lista válida.
            const valido = lista.some(
                (item) => normalizarTexto(item) === municipioNormalizado
            );
            // Si no coincide, marca error de relación inválida.
            if (!valido) {
                // Muestra error de relación cuando corresponda.
                if (shouldShowError("municipio")) {
                    // Informa incoherencia entre departamento y municipio.
                    setError("error-municipio", "El municipio no coincide con el departamento.");
                }
                // Acumula error.
                hasErrors = true;
            } else {
                // Si es válido, limpia error de municipio.
                setError("error-municipio", "");
            }
        } else {
            // Si no hay departamento, limpia estado residual de municipio.
            setError("error-municipio", "");
        }

        // Devuelve true cuando no se acumuló ningún error.
        return !hasErrors;
    };

    // Validación en tiempo real
    // Define mapeo de claves de validación con sus campos DOM.
    const fieldMap = [
        // Campo nombre.
        { key: "nombre", el: nombreInput },
        // Campo teléfono.
        { key: "telefono", el: telefonoInput },
        // Campo correo.
        { key: "email", el: emailInput },
        // Campo departamento.
        { key: "departamento", el: departamentoSelect },
        // Campo municipio.
        { key: "municipio", el: municipioSelect },
    ];

    // Recorre cada campo para enlazar validación reactiva.
    fieldMap.forEach(({ key, el }) => {
        // Al escribir, marca campo tocado y revalida.
        el?.addEventListener("input", function () {
            // Registra interacción del campo.
            touchedFields.add(key);
            // Ejecuta validación global.
            validate();
        });
        // Al cambiar valor, marca campo tocado y revalida.
        el?.addEventListener("change", function () {
            // Registra interacción del campo.
            touchedFields.add(key);
            // Ejecuta validación global.
            validate();
        });
        // Al perder foco, marca campo tocado y revalida.
        el?.addEventListener("blur", function () {
            // Registra interacción del campo.
            touchedFields.add(key);
            // Ejecuta validación global.
            validate();
        });
        // En cada escritura, limpia estado persistido del paso 1.
        el?.addEventListener("input", persistStep1Fields);
        // En cada cambio, limpia estado persistido del paso 1.
        el?.addEventListener("change", persistStep1Fields);
    });

    // Cuando cambia departamento, repuebla municipios y revalida dependencia.
    departamentoSelect?.addEventListener("change", function () {
        // Actualiza lista de municipios según nuevo departamento.
        poblarMunicipios();
        // Guarda municipio actual como previo para futuras restauraciones.
        municipioPrevio = municipioSelect?.value || "";
        // Marca departamento como campo tocado.
        touchedFields.add("departamento");
        // Reejecuta validación general.
        validate();
    });

    // Restaura estado inicial definido por el flujo del paso 1.
    restoreStep1Fields();
    // Limpia cualquier residuo de storage al cargar.
    persistStep1Fields();

    // Inicializa municipios al cargar
    // Ejecuta poblamiento inicial para que el select no quede vacío.
    poblarMunicipios();

    // Si el backend envió municipio seleccionado, lo asigna explícitamente.
    if (municipioSelect?.dataset.selectedMunicipio) {
        // Aplica valor inicial del municipio al select.
        municipioSelect.value = municipioSelect.dataset.selectedMunicipio;
    }

    // Si existe error de servidor en nombre, lo muestra al cargar.
    if (serverNombreError) {
        // Pinta mensaje de servidor para nombre.
        setError("error-nombre", serverNombreError);
    }
    // Si existe error de servidor en teléfono, lo muestra al cargar.
    if (serverTelefonoError) {
        // Pinta mensaje de servidor para teléfono.
        setError("error-telefono", serverTelefonoError);
    }
    // Si existe error de servidor en email, lo muestra al cargar.
    if (serverEmailError) {
        // Pinta mensaje de servidor para email.
        setError("error-email", serverEmailError);
    }
    // Si existe error de servidor en departamento, lo muestra al cargar.
    if (serverDepartamentoError) {
        // Pinta mensaje de servidor para departamento.
        setError("error-departamento", serverDepartamentoError);
    }
    // Si existe error de servidor en municipio, lo muestra al cargar.
    if (serverMunicipioError) {
        // Pinta mensaje de servidor para municipio.
        setError("error-municipio", serverMunicipioError);
    }

    // Bloquea envío si hay errores
    // Intercepta envío para validar antes de enviar al backend.
    form.addEventListener("submit", function (event) {
        // Marca que el usuario ya intentó enviar el formulario.
        submitAttempted = true;
        // Si la validación falla, evita el submit.
        if (!validate()) {
            // Cancela el envío del formulario.
            event.preventDefault();
            // Finaliza para no ejecutar lógica posterior.
            return;
        }
        // Si todo es válido, limpia estado temporal del paso 1.
        persistStep1Fields();
    });
});