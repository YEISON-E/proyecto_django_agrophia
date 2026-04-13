/**
 * CREATE SHOP - PASO 2
 *
 * Valida horario comercial:
 * - Hora de apertura obligatoria
 * - Hora de cierre obligatoria
 * - Hora de cierre mayor que la apertura
 */
// Espera a que el DOM esté disponible antes de inicializar lógica del paso 2.
document.addEventListener("DOMContentLoaded", function () {
    // Formulario de paso 2
    // Obtiene el formulario principal del segundo paso.
    const form = document.getElementById("create-shop-step2-form");
    // Si no existe el formulario, detiene la ejecución.
    if (!form) {
        // Sale tempranamente para evitar errores por referencias nulas.
        return;
    }

    // Recupera identificador de flujo para distinguir datos entre sesiones.
    const flowId = form.dataset.shopFlowId || "default";
    // Construye clave única de sessionStorage para el paso 2.
    const STEP2_STORAGE_KEY = `agrophia.create_shop.step2.${flowId}`;
    // Lee posible error del servidor asociado al horario de cierre.
    const serverHorarioError = document.getElementById("error-hora-cierre")?.dataset.serverError || "";
    // Lee posible error del servidor asociado a dirección.
    const serverDireccionError = document.getElementById("error-direccion")?.dataset.serverError || "";
    // Lee posible error del servidor asociado a descripción.
    const serverDescripcionError = document.getElementById("error-descripcion")?.dataset.serverError || "";

    // Select que indica si la tienda tendrá punto físico.
    const puntoFisicoSelect = document.getElementById("tiene_punto_fisico");
    // Contenedor visual de campos físicos (horario y dirección).
    const physicalFields = document.getElementById("shop-physical-fields");
    // Tarjeta contenedora principal del paso 2.
    const shopCard = form.closest(".shop");
    // Input de hora de apertura.
    const horaAperturaInput = document.getElementById("hora_apertura");
    // Input de hora de cierre.
    const horaCierreInput = document.getElementById("hora_cierre");
    // Input de dirección física.
    const direccionInput = document.getElementById("direccion");
    // Textarea de descripción de la tienda.
    const descripcionInput = form.querySelector("textarea[name='descripcion']");
    // Conjunto de campos ya interactuados por el usuario.
    const touchedFields = new Set();
    // Bandera para saber si ya hubo intento de envío.
    let submitAttempted = false;

    // Persiste en sessionStorage los valores del paso 2 para recuperar estado.
    const persistStep2Fields = () => {
        // Encapsula operaciones de storage para tolerar fallos del navegador.
        try {
            // Construye payload serializable con valores actuales del formulario.
            const payload = {
                // Guarda opción de punto físico con valor por defecto "no".
                tiene_punto_fisico: puntoFisicoSelect?.value || "no",
                // Guarda hora de apertura o cadena vacía.
                hora_apertura: horaAperturaInput?.value || "",
                // Guarda hora de cierre o cadena vacía.
                hora_cierre: horaCierreInput?.value || "",
                // Guarda dirección o cadena vacía.
                direccion: direccionInput?.value || "",
                // Guarda descripción o cadena vacía.
                descripcion: descripcionInput?.value || "",
            };
            // Serializa y guarda el payload en sessionStorage.
            sessionStorage.setItem(STEP2_STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
            // Notifica en consola si no pudo persistir datos.
            console.warn("No se pudo guardar el paso 2 de la tienda en sessionStorage.", error);
        }
    };

    // Restaura desde sessionStorage los valores del paso 2 cuando existan.
    const restoreStep2Fields = () => {
        // Protege lectura y parseo contra datos corruptos o bloqueos.
        try {
            // Lee texto crudo almacenado para el paso 2.
            const raw = sessionStorage.getItem(STEP2_STORAGE_KEY);
            // Si no hay datos guardados, no restaura nada.
            if (!raw) {
                // Sale sin aplicar cambios.
                return;
            }
            // Convierte el texto JSON a objeto usable.
            const saved = JSON.parse(raw);
            // Si el select existe y está vacío, aplica valor guardado de punto físico.
            if (puntoFisicoSelect && !puntoFisicoSelect.value && saved.tiene_punto_fisico) {
                // Asigna valor de punto físico guardado.
                puntoFisicoSelect.value = saved.tiene_punto_fisico;
            }
            // Refuerza asignación del valor guardado cuando exista.
            if (puntoFisicoSelect && saved.tiene_punto_fisico) {
                // Reasigna por consistencia con estado persistido.
                puntoFisicoSelect.value = saved.tiene_punto_fisico;
            }
            // Restaura hora de apertura solo si el input está vacío.
            if (horaAperturaInput && !horaAperturaInput.value && saved.hora_apertura) {
                // Aplica hora de apertura guardada.
                horaAperturaInput.value = saved.hora_apertura;
            }
            // Restaura hora de cierre solo si el input está vacío.
            if (horaCierreInput && !horaCierreInput.value && saved.hora_cierre) {
                // Aplica hora de cierre guardada.
                horaCierreInput.value = saved.hora_cierre;
            }
            // Restaura dirección solo si el input está vacío.
            if (direccionInput && !direccionInput.value && saved.direccion) {
                // Aplica dirección guardada.
                direccionInput.value = saved.direccion;
            }
            // Restaura descripción solo si la textarea está vacía.
            if (descripcionInput && !descripcionInput.value && saved.descripcion) {
                // Aplica descripción guardada.
                descripcionInput.value = saved.descripcion;
            }
        } catch (error) {
            // Notifica en consola si falla lectura o parseo de sessionStorage.
            console.warn("No se pudo restaurar el paso 2 de la tienda desde sessionStorage.", error);
        }
    };

    // Indica si el flujo actual requiere datos de punto físico.
    const usaPuntoFisico = () => puntoFisicoSelect?.value !== "no";

    // Activa o desactiva visual y semánticamente los campos de punto físico.
    const togglePhysicalFields = () => {
        // Define si se deben mostrar campos físicos según la selección.
        const mostrar = usaPuntoFisico();

        // Ajusta clase de layout en grilla para el estado mostrado.
        form.classList.toggle("create-shop-step2--grid", mostrar);
        // Ajusta clase auxiliar de visibilidad de campos físicos.
        form.classList.toggle("show-physical-fields", mostrar);
        // Compacta o expande el ancho de la tarjeta principal según el estado.
        shopCard?.classList.toggle("shop--compact-step2", !mostrar);

        // Si existe el contenedor, permite que CSS controle su visualización.
        if (physicalFields) {
            // Limpia override inline para no forzar display específico.
            physicalFields.style.display = "";
        }

        // Marca requerida la hora de apertura solo si hay punto físico.
        if (horaAperturaInput) {
            // Activa/desactiva required dinámicamente.
            horaAperturaInput.required = mostrar;
        }
        // Marca requerida la hora de cierre solo si hay punto físico.
        if (horaCierreInput) {
            // Activa/desactiva required dinámicamente.
            horaCierreInput.required = mostrar;
        }
        // Marca requerida la dirección solo si hay punto físico.
        if (direccionInput) {
            // Activa/desactiva required dinámicamente.
            direccionInput.required = mostrar;
        }

        // Si no se muestra sección física, limpia mensajes de error asociados.
        if (!mostrar) {
            // Limpia error de hora de apertura.
            setError("error-hora-apertura", "");
            // Limpia error de hora de cierre.
            setError("error-hora-cierre", "");
            // Limpia error de dirección.
            setError("error-direccion", "");
        }
    };

    // Define cuándo un campo debe mostrar mensaje de error.
    const shouldShowError = (fieldKey) => submitAttempted || touchedFields.has(fieldKey);

    // Valida longitud máxima de descripción opcional.
    const validateDescripcion = () => {
        const descripcion = descripcionInput?.value || "";
        if (descripcion.length > 255) {
            if (shouldShowError("descripcion")) {
                setError("error-descripcion", "La descripción no puede superar los 255 caracteres.");
            }
            return false;
        }
        setError("error-descripcion", "");
        return true;
    };

    // Helper para pintar errores inline
    // Muestra u oculta un mensaje de error en el contenedor indicado.
    const setError = (id, message) => {
        // Busca el contenedor de error por su id.
        const el = document.getElementById(id);
        // Si no existe, omite operación para evitar errores.
        if (!el) {
            // Sale de la función.
            return;
        }
        // Si hay mensaje, activa el estado visible del error.
        if (message) {
            // Asigna el texto del mensaje.
            el.textContent = message;
            // Agrega clase visual de error visible.
            el.classList.add("is-visible");
            // Fuerza display flex para respetar diseño del bloque.
            el.style.display = "flex";
        } else {
            // Si no hay mensaje, limpia contenido textual.
            el.textContent = "";
            // Quita clase visual de estado visible.
            el.classList.remove("is-visible");
            // Oculta el contenedor de error.
            el.style.display = "none";
        }
    };

    // Reglas de validación para el rango horario
    // Valida horario y dirección cuando aplica punto físico.
    const validateHorario = () => {
        // Si no usa punto físico, no exige horario ni dirección.
        if (!usaPuntoFisico()) {
            // Limpia error de apertura al no aplicar.
            setError("error-hora-apertura", "");
            // Limpia error de cierre al no aplicar.
            setError("error-hora-cierre", "");
            // Limpia error de dirección al no aplicar.
            setError("error-direccion", "");
            // Considera la validación como correcta en este escenario.
            return true;
        }

        // Bandera de acumulación de errores.
        let hasErrors = false;

        // Captura hora de apertura actual.
        const apertura = horaAperturaInput?.value || "";
        // Captura hora de cierre actual.
        const cierre = horaCierreInput?.value || "";
        // Captura dirección actual, eliminando espacios laterales.
        const direccion = direccionInput?.value.trim() || "";

        // Regla: apertura obligatoria.
        if (!apertura) {
            // Muestra error solo si el campo debe mostrarlo.
            if (shouldShowError("hora_apertura")) {
                // Informa obligatoriedad de la hora de apertura.
                setError("error-hora-apertura", "La hora de apertura es obligatoria.");
            }
            // Acumula error de validación.
            hasErrors = true;
        } else {
            // Si cumple, limpia error de apertura.
            setError("error-hora-apertura", "");
        }

        // Regla: cierre obligatorio.
        if (!cierre) {
            // Muestra error solo si el campo debe mostrarlo.
            if (shouldShowError("hora_cierre")) {
                // Informa obligatoriedad de la hora de cierre.
                setError("error-hora-cierre", "La hora de cierre es obligatoria.");
            }
            // Acumula error de validación.
            hasErrors = true;
        } else {
            // Si cumple, limpia error de cierre.
            setError("error-hora-cierre", "");
        }

        // Regla: cierre debe ser mayor que apertura.
        if (apertura && cierre && cierre <= apertura) {
            // Muestra error de orden temporal cuando corresponda.
            if (shouldShowError("hora_cierre")) {
                // Informa que el cierre debe ser posterior a apertura.
                setError("error-hora-cierre", "La hora de cierre debe ser mayor que la de apertura.");
            }
            // Acumula error de validación.
            hasErrors = true;
        }

        // Regla: dirección obligatoria cuando hay punto físico.
        if (!direccion) {
            // Muestra error solo si el campo debe mostrarlo.
            if (shouldShowError("direccion")) {
                // Informa obligatoriedad de dirección en este caso.
                setError("error-direccion", "La dirección es obligatoria si tienes punto físico.");
            }
            // Acumula error de validación.
            hasErrors = true;
        } else {
            // Si cumple, limpia error de dirección.
            setError("error-direccion", "");
        }

        // Devuelve true si no se encontraron errores.
        return !hasErrors;
    };

    // Validación en tiempo real al cambiar horas
    // Al cambiar si hay punto físico, ajusta campos requeridos y revalida.
    puntoFisicoSelect?.addEventListener("change", function () {
        // Marca interacción del campo en el set de tocados.
        touchedFields.add("tiene_punto_fisico");
        // Recalcula estado visual/required de campos físicos.
        togglePhysicalFields();
        // Reejecuta validación del bloque horario.
        validateHorario();
    });
    // Al escribir apertura, marca campo y revalida.
    horaAperturaInput?.addEventListener("input", function () {
        // Marca apertura como tocado.
        touchedFields.add("hora_apertura");
        // Revalida horario.
        validateHorario();
    });
    // Al perder foco en apertura, marca campo y revalida.
    horaAperturaInput?.addEventListener("blur", function () {
        // Marca apertura como tocado.
        touchedFields.add("hora_apertura");
        // Revalida horario.
        validateHorario();
    });
    // Al escribir cierre, marca campo y revalida.
    horaCierreInput?.addEventListener("input", function () {
        // Marca cierre como tocado.
        touchedFields.add("hora_cierre");
        // Revalida horario.
        validateHorario();
    });
    // Al perder foco en cierre, marca campo y revalida.
    horaCierreInput?.addEventListener("blur", function () {
        // Marca cierre como tocado.
        touchedFields.add("hora_cierre");
        // Revalida horario.
        validateHorario();
    });
    // Al escribir dirección, marca campo y revalida.
    direccionInput?.addEventListener("input", function () {
        // Marca dirección como tocada.
        touchedFields.add("direccion");
        // Revalida horario/dirección.
        validateHorario();
    });
    // Al perder foco en dirección, marca campo y revalida.
    direccionInput?.addEventListener("blur", function () {
        // Marca dirección como tocada.
        touchedFields.add("direccion");
        // Revalida horario/dirección.
        validateHorario();
    });
    // Al escribir descripción, marca campo y valida longitud.
    descripcionInput?.addEventListener("input", function () {
        touchedFields.add("descripcion");
        validateDescripcion();
    });
    // Al perder foco en descripción, marca campo y valida longitud.
    descripcionInput?.addEventListener("blur", function () {
        touchedFields.add("descripcion");
        validateDescripcion();
    });
    // Registra persistencia en cambios de todos los campos relevantes del paso 2.
    [puntoFisicoSelect, horaAperturaInput, horaCierreInput, direccionInput, descripcionInput].forEach((field) => {
        // Guarda estado al escribir en el campo.
        field?.addEventListener("input", persistStep2Fields);
        // Guarda estado al cambiar el campo.
        field?.addEventListener("change", persistStep2Fields);
    });

    // Restaura valores persistidos antes de ajustar UI.
    restoreStep2Fields();

    // Aplica estado inicial de visibilidad y required de campos físicos.
    togglePhysicalFields();

    // Si backend reportó error horario, se muestra al cargar.
    if (serverHorarioError) {
        // Pinta error proveniente del servidor en hora de cierre.
        setError("error-hora-cierre", serverHorarioError);
    }
    // Si backend reportó error de dirección, se muestra al cargar.
    if (serverDireccionError) {
        // Pinta error proveniente del servidor en dirección.
        setError("error-direccion", serverDireccionError);
    }
    // Si backend reportó error de descripción, se muestra al cargar.
    if (serverDescripcionError) {
        setError("error-descripcion", serverDescripcionError);
    }

    // Previene submit si el horario es inválido
    // Intercepta el envío para validar y persistir estado correctamente.
    form.addEventListener("submit", function (event) {
        // Lee acción del formulario para distinguir "volver" de "continuar".
        const actionInput = document.getElementById("create-shop-step2-action");
        // Si la acción es volver, no bloquea y solo persiste datos.
        if (actionInput && actionInput.value === "back") {
            // Guarda estado actual antes de regresar al paso anterior.
            persistStep2Fields();
            // Sale sin validar para permitir navegación de retorno.
            return;
        }

        // Marca que ya hubo intento de submit para habilitar mensajes.
        submitAttempted = true;
        // Si validación falla, cancela el envío.
        if (!validateHorario() || !validateDescripcion()) {
            // Previene submit al backend con datos inválidos.
            event.preventDefault();
            // Finaliza ejecución del manejador.
            return;
        }
        // Si todo es válido, persiste estado final del paso 2.
        persistStep2Fields();
    });
});