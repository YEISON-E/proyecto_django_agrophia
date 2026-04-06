// Espera a que el documento HTML termine de cargar antes de inicializar la logica.
document.addEventListener("DOMContentLoaded", function () {
    // Clave usada para guardar/restaurar datos del paso 1 en sessionStorage.
    const STEP1_STORAGE_KEY = "agrophia.create_product.step1";
    // Input tipo file donde se seleccionan imagenes del producto.
    const input = document.getElementById("input-fotos-producto");
    // Zona de arrastre (drag and drop) para cargar imagenes.
    const dropzone = document.getElementById("dropzone-fotos-producto");
    // Contenedor donde se dibuja la previsualizacion de imagenes.
    const previewGrid = document.getElementById("fotos-preview");
    // Nodo que muestra contador de imagenes nuevas/guardadas.
    const counter = document.getElementById("fotos-counter");

    // Si faltan nodos esenciales, cancela la inicializacion.
    if (!input || !dropzone || !previewGrid || !counter) {
        return;
    }

    // Limite maximo de fotos permitido por producto.
    const maxFotos = 8;
    // Arreglo en memoria con archivos seleccionados en esta sesion.
    let selectedFiles = [];

    // Input del nombre del producto.
    const nombreInput = document.getElementById("nombre-producto");
    // Select del tipo de producto.
    const tipoSelect = document.getElementById("tipo-producto");
    // Grupo visual para capturar tipo personalizado cuando tipo = Otros.
    const tipoOtroGroup = document.getElementById("group-tipo-producto-otro");
    // Input del tipo personalizado.
    const tipoOtroInput = document.getElementById("tipo-producto-otro");
    // Select de unidad de medida.
    const unidadSelect = document.getElementById("unidad-producto");
    // Boton para avanzar al siguiente paso del formulario.
    const nextStepButton = document.getElementById("btn-next-step-producto");
    // Formulario del paso 1.
    const step1Form = document.getElementById("create-product-step1-form");
    // Cantidad de imagenes temporales ya guardadas en servidor (si existen).
    const existingTempImagesCount = Number(step1Form?.dataset.existingTempImages || 0);

    // Guarda los campos clave del paso 1 en sessionStorage.
    const persistStep1Fields = () => {
        try {
            // Construye payload con valores actuales del formulario.
            const payload = {
                nombre: nombreInput?.value || "",
                tipo: tipoSelect?.value || "",
                tipo_otro: tipoOtroInput?.value || "",
                unidad: unidadSelect?.value || "",
            };
            // Persiste el payload serializado como JSON.
            sessionStorage.setItem(STEP1_STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
            // Log en consola si el guardado falla.
            console.warn("No se pudo guardar el paso 1 del producto en sessionStorage.", error);
        }
    };

    // Restaura campos del paso 1 desde sessionStorage cuando aplica.
    const restoreStep1Fields = () => {
        try {
            // Lee valor bruto guardado en sessionStorage.
            const raw = sessionStorage.getItem(STEP1_STORAGE_KEY);
            // Si no hay datos guardados, no hace nada.
            if (!raw) {
                return;
            }
            // Convierte el JSON guardado a objeto.
            const saved = JSON.parse(raw);
            // Restaura nombre solo si el input esta vacio actualmente.
            if (nombreInput && !nombreInput.value && saved.nombre) {
                nombreInput.value = saved.nombre;
            }
            // Restaura tipo solo si el select esta vacio actualmente.
            if (tipoSelect && !tipoSelect.value && saved.tipo) {
                tipoSelect.value = saved.tipo;
            }
            // Restaura tipo personalizado solo si el campo esta vacio.
            if (tipoOtroInput && !tipoOtroInput.value && saved.tipo_otro) {
                tipoOtroInput.value = saved.tipo_otro;
            }
            // Restaura unidad solo si el select aun no tiene valor.
            if (unidadSelect && !unidadSelect.value && saved.unidad) {
                unidadSelect.value = saved.unidad;
            }
        } catch (error) {
            // Log si ocurre error al leer o parsear datos guardados.
            console.warn("No se pudo restaurar el paso 1 del producto desde sessionStorage.", error);
        }
    };

    // Mapa de unidades permitidas por cada tipo de producto.
    const unidadesPorTipo = {
        Frutas: ["Libra", "Kilo", "Arroba", "Unidad"],
        Vegetales: ["Libra", "Kilo", "Arroba", "Unidad"],
        "Lácteos": ["Litro", "Unidad"],
        Carne: ["Libra", "Kilo", "Arroba", "Unidad"],
        Granos: ["Libra", "Kilo", "Arroba", "Unidad"],
        Otros: ["Libra", "Kilo", "Arroba", "Litro", "Unidad"],
    };
    // Patron de caracteres permitidos para nombre del producto.
    const allowedProductNamePattern = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s.,\-]+$/;

    // Helper para mostrar u ocultar mensajes de error por id.
    const setError = (id, message) => {
        // Obtiene nodo de error por su id.
        const el = document.getElementById(id);
        // Si el nodo no existe, termina.
        if (!el) {
            return;
        }
        // Si hay mensaje, lo muestra.
        if (message) {
            el.textContent = message;
            el.style.display = "block";
        } else {
            // Si no hay mensaje, limpia y oculta el error.
            el.textContent = "";
            el.style.display = "none";
        }
    };

    // Valida todas las reglas del paso 1.
    const validateStep1 = () => {
        // Bandera acumuladora de errores.
        let hasErrors = false;

        // Valida que haya al menos una imagen (nueva o temporal).
        if (selectedFiles.length === 0 && existingTempImagesCount === 0) {
            setError("error-fotos-producto", "Debes cargar al menos una imagen.");
            hasErrors = true;
        } else {
            setError("error-fotos-producto", "");
        }

        // Lee y normaliza nombre del producto.
        const nombre = (nombreInput?.value || "").trim();
        // Regla: nombre obligatorio.
        if (!nombre) {
            setError("error-nombre-producto", "El nombre del producto es obligatorio.");
            hasErrors = true;
        // Regla: longitud minima 3.
        } else if (nombre.length < 3) {
            setError("error-nombre-producto", "El nombre debe tener al menos 3 caracteres.");
            hasErrors = true;
        // Regla: longitud maxima 120.
        } else if (nombre.length > 120) {
            setError("error-nombre-producto", "El nombre no debe superar 120 caracteres.");
            hasErrors = true;
        // Regla: caracteres permitidos.
        } else if (!allowedProductNamePattern.test(nombre)) {
            setError("error-nombre-producto", "El nombre contiene caracteres no permitidos.");
            hasErrors = true;
        } else {
            // Limpia error si pasa validaciones de nombre.
            setError("error-nombre-producto", "");
        }

        // Lee valor actual del tipo de producto.
        const tipo = tipoSelect?.value || "";
        // Regla: tipo obligatorio.
        if (!tipo) {
            setError("error-tipo-producto", "Selecciona un tipo de producto.");
            hasErrors = true;
        } else {
            // Limpia error si tipo es valido.
            setError("error-tipo-producto", "");
        }

        // Determina si debe mostrarse campo tipo personalizado.
        const requiereTipoOtro = tipo === "Otros";
        // Muestra/oculta grupo del campo otro tipo.
        if (tipoOtroGroup) {
            tipoOtroGroup.style.display = requiereTipoOtro ? "flex" : "none";
        }

        // Valida campo tipo personalizado cuando aplica.
        if (requiereTipoOtro) {
            // Lee valor normalizado de tipo personalizado.
            const tipoOtro = (tipoOtroInput?.value || "").trim();
            // Regla: obligatorio cuando tipo = Otros.
            if (!tipoOtro) {
                setError("error-tipo-producto-otro", "Escribe el tipo de producto.");
                hasErrors = true;
            // Regla: minimo 3 caracteres.
            } else if (tipoOtro.length < 3) {
                setError("error-tipo-producto-otro", "Debe tener al menos 3 caracteres.");
                hasErrors = true;
            } else {
                // Limpia error si valor es valido.
                setError("error-tipo-producto-otro", "");
            }
        } else {
            // Limpia error del campo cuando no aplica.
            setError("error-tipo-producto-otro", "");
            // Limpia valor residual del input otro tipo.
            if (tipoOtroInput) {
                tipoOtroInput.value = "";
            }
        }

        // Lee unidad elegida actualmente.
        const unidad = unidadSelect?.value || "";
        // Obtiene listado permitido de unidades segun tipo.
        const unidadesPermitidas = unidadesPorTipo[tipo] || [];
        // Regla: unidad obligatoria.
        if (!unidad) {
            setError("error-unidad-producto", "Selecciona una unidad de medida.");
            hasErrors = true;
        // Regla: unidad debe pertenecer a las permitidas del tipo.
        } else if (tipo && !unidadesPermitidas.includes(unidad)) {
            setError("error-unidad-producto", `La unidad no aplica para ${tipo}.`);
            hasErrors = true;
        } else {
            // Limpia error si unidad es valida.
            setError("error-unidad-producto", "");
        }

        // Devuelve true si no se encontraron errores.
        return !hasErrors;
    };

    // Compara dos archivos por nombre, tamano y fecha para detectar duplicados.
    const isSameFile = (fileA, fileB) => (
        fileA.name === fileB.name
        && fileA.size === fileB.size
        && fileA.lastModified === fileB.lastModified
    );

    // Sincroniza selectedFiles con input.files usando DataTransfer.
    const syncInputFiles = () => {
        // Crea contenedor temporal de archivos.
        const dataTransfer = new DataTransfer();
        // Agrega cada archivo seleccionado.
        selectedFiles.forEach((file) => dataTransfer.items.add(file));
        // Asigna resultado al input file.
        input.files = dataTransfer.files;
    };

    // Actualiza texto del contador de imagenes.
    const updateCounter = () => {
        // Calcula total sumando nuevas + guardadas.
        const total = selectedFiles.length + existingTempImagesCount;
        // Renderiza el estado del contador en interfaz.
        counter.textContent = `${selectedFiles.length} nuevas | ${existingTempImagesCount} guardadas | total ${total}/${maxFotos}`;
    };

    // Dibuja previsualizacion de imagenes seleccionadas.
    const renderPreview = () => {
        // Limpia grid antes de redibujar.
        previewGrid.innerHTML = "";

        // Recorre archivos seleccionados.
        selectedFiles.forEach((file, index) => {
            // Crea tarjeta visual de preview.
            const card = document.createElement("div");
            card.className = "product-form__preview-item";

            // Crea elemento img para preview.
            const image = document.createElement("img");
            image.className = "product-form__preview-image";
            image.alt = `Foto ${index + 1}`;

            // Crea boton para remover imagen del listado.
            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "product-form__preview-remove";
            removeButton.textContent = "×";

            // Al hacer click, elimina archivo y refresca UI.
            removeButton.addEventListener("click", () => {
                selectedFiles.splice(index, 1);
                syncInputFiles();
                updateCounter();
                renderPreview();
            });

            // Crea URL temporal del archivo para mostrar preview.
            const objectUrl = URL.createObjectURL(file);
            image.src = objectUrl;
            // Libera URL temporal cuando la imagen termina de cargar.
            image.onload = () => URL.revokeObjectURL(objectUrl);

            // Agrega imagen y boton a la card.
            card.appendChild(image);
            card.appendChild(removeButton);
            // Agrega card al grid de previews.
            previewGrid.appendChild(card);
        });
    };

    // Agrega archivos nuevos al arreglo, aplica deduplicacion y limite maximo.
    const addFiles = (fileList) => {
        // Convierte FileList a array y filtra solo imagenes.
        const incoming = Array.from(fileList).filter((file) => file.type.startsWith("image/"));

        // Recorre cada archivo entrante.
        incoming.forEach((file) => {
            // Verifica si ya existe en selectedFiles.
            const exists = selectedFiles.some((item) => isSameFile(item, file));
            // Agrega solo si no existe y no supera maximo permitido.
            if (!exists && (existingTempImagesCount + selectedFiles.length) < maxFotos) {
                selectedFiles.push(file);
            }
        });

        // Sincroniza input, contador y preview despues de agregar.
        syncInputFiles();
        updateCounter();
        renderPreview();
    };

    // Regenera opciones de unidad segun tipo seleccionado.
    const updateUnidadOptions = () => {
        // Si no existe select de unidad, termina.
        if (!unidadSelect) {
            return;
        }

        // Lee tipo actual.
        const tipo = tipoSelect?.value || "";
        // Obtiene unidades validas para el tipo.
        const unidades = unidadesPorTipo[tipo] || [];
        // Guarda valor previo para intentar preservarlo.
        const valorActual = unidadSelect.value;

        // Reinicia opciones con placeholder.
        unidadSelect.innerHTML = '<option value="">-- Selecciona --</option>';

        // Inserta cada opcion de unidad permitida.
        unidades.forEach((unidad) => {
            const option = document.createElement("option");
            option.value = unidad;
            option.textContent = unidad;
            unidadSelect.appendChild(option);
        });

        // Si valor previo aun es valido, lo conserva; si no, limpia.
        if (unidades.includes(valorActual)) {
            unidadSelect.value = valorActual;
        } else {
            unidadSelect.value = "";
        }
    };

    // Al cambiar input file, agrega archivos y valida paso.
    input.addEventListener("change", () => {
        addFiles(input.files);
        validateStep1();
    });

    // Para cada campo clave, valida y persiste en input/change.
    [nombreInput, tipoSelect, tipoOtroInput, unidadSelect].forEach((field) => {
        field?.addEventListener("input", validateStep1);
        field?.addEventListener("change", validateStep1);
        field?.addEventListener("input", persistStep1Fields);
        field?.addEventListener("change", persistStep1Fields);
    });

    // Al cambiar tipo, actualiza unidades disponibles y revalida.
    tipoSelect?.addEventListener("change", () => {
        updateUnidadOptions();
        validateStep1();
    });

    // Bloquea avance al siguiente paso si hay errores de validacion.
    nextStepButton?.addEventListener("click", (event) => {
        if (!validateStep1()) {
            event.preventDefault();
        }
    });

    // En submit del paso 1, valida y persiste campos antes de enviar.
    step1Form?.addEventListener("submit", (event) => {
        if (!validateStep1()) {
            event.preventDefault();
            return;
        }
        persistStep1Fields();
    });

    // Marca visualmente dropzone cuando entran archivos arrastrados.
    ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();
            dropzone.classList.add("product-form__dropzone--dragover");
        });
    });

    // Quita estado visual de drag al salir o soltar.
    ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();
            dropzone.classList.remove("product-form__dropzone--dragover");
        });
    });

    // Al soltar archivos en dropzone, los agrega si existen.
    dropzone.addEventListener("drop", (event) => {
        const files = event.dataTransfer?.files;
        if (files && files.length) {
            addFiles(files);
        }
    });

    // Restaura datos del paso 1 guardados previamente.
    restoreStep1Fields();
    // Reconstruye opciones de unidad segun tipo restaurado/actual.
    updateUnidadOptions();

    // Intenta restaurar unidad si existe en sessionStorage y campo esta vacio.
    try {
        const raw = sessionStorage.getItem(STEP1_STORAGE_KEY);
        if (raw) {
            const saved = JSON.parse(raw);
            if (unidadSelect && !unidadSelect.value && saved.unidad) {
                unidadSelect.value = saved.unidad;
            }
        }
    } catch (error) {
        // Log si no se puede restaurar unidad por error de parseo/lectura.
        console.warn("No se pudo restaurar la unidad del paso 1 del producto.", error);
    }

    // Si tipo actual es Otros, asegura que grupo de tipo personalizado sea visible.
    if (tipoSelect?.value === "Otros" && tipoOtroGroup) {
        tipoOtroGroup.style.display = "flex";
    }

    // Render inicial del contador al cargar pagina.
    updateCounter();
});
