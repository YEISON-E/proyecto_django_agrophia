document.addEventListener("DOMContentLoaded", function () {
    const STEP1_STORAGE_KEY = "agrophia.create_product.step1";
    const input = document.getElementById("input-fotos-producto");
    const dropzone = document.getElementById("dropzone-fotos-producto");
    const previewGrid = document.getElementById("fotos-preview");
    const counter = document.getElementById("fotos-counter");

    if (!input || !dropzone || !previewGrid || !counter) {
        return;
    }

    const maxFotos = 8;
    let selectedFiles = [];

    const nombreInput = document.getElementById("nombre-producto");
    const tipoSelect = document.getElementById("tipo-producto");
    const tipoOtroGroup = document.getElementById("group-tipo-producto-otro");
    const tipoOtroInput = document.getElementById("tipo-producto-otro");
    const unidadSelect = document.getElementById("unidad-producto");
    const nextStepButton = document.getElementById("btn-next-step-producto");
    const step1Form = document.getElementById("create-product-step1-form");
    const existingTempImagesCount = Number(step1Form?.dataset.existingTempImages || 0);

    const persistStep1Fields = () => {
        try {
            const payload = {
                nombre: nombreInput?.value || "",
                tipo: tipoSelect?.value || "",
                tipo_otro: tipoOtroInput?.value || "",
                unidad: unidadSelect?.value || "",
            };
            sessionStorage.setItem(STEP1_STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
            console.warn("No se pudo guardar el paso 1 del producto en sessionStorage.", error);
        }
    };

    const restoreStep1Fields = () => {
        try {
            const raw = sessionStorage.getItem(STEP1_STORAGE_KEY);
            if (!raw) {
                return;
            }
            const saved = JSON.parse(raw);
            if (nombreInput && !nombreInput.value && saved.nombre) {
                nombreInput.value = saved.nombre;
            }
            if (tipoSelect && !tipoSelect.value && saved.tipo) {
                tipoSelect.value = saved.tipo;
            }
            if (tipoOtroInput && !tipoOtroInput.value && saved.tipo_otro) {
                tipoOtroInput.value = saved.tipo_otro;
            }
            if (unidadSelect && !unidadSelect.value && saved.unidad) {
                unidadSelect.value = saved.unidad;
            }
        } catch (error) {
            console.warn("No se pudo restaurar el paso 1 del producto desde sessionStorage.", error);
        }
    };

    const unidadesPorTipo = {
        Frutas: ["Libra", "Kilo", "Arroba"],
        Vegetales: ["Libra", "Kilo", "Arroba"],
        "Lácteos": ["Litro"],
        Carne: ["Libra", "Kilo", "Arroba"],
        Granos: ["Libra", "Kilo", "Arroba"],
        Otros: ["Libra", "Kilo", "Arroba", "Litro"],
    };
    const allowedProductNamePattern = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s.,\-]+$/;

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

    const validateStep1 = () => {
        let hasErrors = false;

        if (selectedFiles.length === 0 && existingTempImagesCount === 0) {
            setError("error-fotos-producto", "Debes cargar al menos una imagen.");
            hasErrors = true;
        } else {
            setError("error-fotos-producto", "");
        }

        const nombre = (nombreInput?.value || "").trim();
        if (!nombre) {
            setError("error-nombre-producto", "El nombre del producto es obligatorio.");
            hasErrors = true;
        } else if (nombre.length < 3) {
            setError("error-nombre-producto", "El nombre debe tener al menos 3 caracteres.");
            hasErrors = true;
        } else if (nombre.length > 120) {
            setError("error-nombre-producto", "El nombre no debe superar 120 caracteres.");
            hasErrors = true;
        } else if (!allowedProductNamePattern.test(nombre)) {
            setError("error-nombre-producto", "El nombre contiene caracteres no permitidos.");
            hasErrors = true;
        } else {
            setError("error-nombre-producto", "");
        }

        const tipo = tipoSelect?.value || "";
        if (!tipo) {
            setError("error-tipo-producto", "Selecciona un tipo de producto.");
            hasErrors = true;
        } else {
            setError("error-tipo-producto", "");
        }

        const requiereTipoOtro = tipo === "Otros";
        if (tipoOtroGroup) {
            tipoOtroGroup.style.display = requiereTipoOtro ? "flex" : "none";
        }

        if (requiereTipoOtro) {
            const tipoOtro = (tipoOtroInput?.value || "").trim();
            if (!tipoOtro) {
                setError("error-tipo-producto-otro", "Escribe el tipo de producto.");
                hasErrors = true;
            } else if (tipoOtro.length < 3) {
                setError("error-tipo-producto-otro", "Debe tener al menos 3 caracteres.");
                hasErrors = true;
            } else {
                setError("error-tipo-producto-otro", "");
            }
        } else {
            setError("error-tipo-producto-otro", "");
            if (tipoOtroInput) {
                tipoOtroInput.value = "";
            }
        }

        const unidad = unidadSelect?.value || "";
        const unidadesPermitidas = unidadesPorTipo[tipo] || [];
        if (!unidad) {
            setError("error-unidad-producto", "Selecciona una unidad de medida.");
            hasErrors = true;
        } else if (tipo && !unidadesPermitidas.includes(unidad)) {
            setError("error-unidad-producto", `La unidad no aplica para ${tipo}.`);
            hasErrors = true;
        } else {
            setError("error-unidad-producto", "");
        }

        return !hasErrors;
    };

    const isSameFile = (fileA, fileB) => (
        fileA.name === fileB.name
        && fileA.size === fileB.size
        && fileA.lastModified === fileB.lastModified
    );

    const syncInputFiles = () => {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach((file) => dataTransfer.items.add(file));
        input.files = dataTransfer.files;
    };

    const updateCounter = () => {
        const total = selectedFiles.length + existingTempImagesCount;
        counter.textContent = `${selectedFiles.length} nuevas | ${existingTempImagesCount} guardadas | total ${total}/${maxFotos}`;
    };

    const renderPreview = () => {
        previewGrid.innerHTML = "";

        selectedFiles.forEach((file, index) => {
            const card = document.createElement("div");
            card.className = "product-form__preview-item";

            const image = document.createElement("img");
            image.className = "product-form__preview-image";
            image.alt = `Foto ${index + 1}`;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "product-form__preview-remove";
            removeButton.textContent = "×";

            removeButton.addEventListener("click", () => {
                selectedFiles.splice(index, 1);
                syncInputFiles();
                updateCounter();
                renderPreview();
            });

            const objectUrl = URL.createObjectURL(file);
            image.src = objectUrl;
            image.onload = () => URL.revokeObjectURL(objectUrl);

            card.appendChild(image);
            card.appendChild(removeButton);
            previewGrid.appendChild(card);
        });
    };

    const addFiles = (fileList) => {
        const incoming = Array.from(fileList).filter((file) => file.type.startsWith("image/"));

        incoming.forEach((file) => {
            const exists = selectedFiles.some((item) => isSameFile(item, file));
            if (!exists && (existingTempImagesCount + selectedFiles.length) < maxFotos) {
                selectedFiles.push(file);
            }
        });

        syncInputFiles();
        updateCounter();
        renderPreview();
    };

    const updateUnidadOptions = () => {
        if (!unidadSelect) {
            return;
        }

        const tipo = tipoSelect?.value || "";
        const unidades = unidadesPorTipo[tipo] || [];
        const valorActual = unidadSelect.value;

        unidadSelect.innerHTML = '<option value="">-- Selecciona --</option>';

        unidades.forEach((unidad) => {
            const option = document.createElement("option");
            option.value = unidad;
            option.textContent = unidad;
            unidadSelect.appendChild(option);
        });

        if (unidades.includes(valorActual)) {
            unidadSelect.value = valorActual;
        } else {
            unidadSelect.value = "";
        }
    };

    input.addEventListener("change", () => {
        addFiles(input.files);
        validateStep1();
    });

    [nombreInput, tipoSelect, tipoOtroInput, unidadSelect].forEach((field) => {
        field?.addEventListener("input", validateStep1);
        field?.addEventListener("change", validateStep1);
        field?.addEventListener("input", persistStep1Fields);
        field?.addEventListener("change", persistStep1Fields);
    });

    tipoSelect?.addEventListener("change", () => {
        updateUnidadOptions();
        validateStep1();
    });

    nextStepButton?.addEventListener("click", (event) => {
        if (!validateStep1()) {
            event.preventDefault();
        }
    });

    step1Form?.addEventListener("submit", (event) => {
        if (!validateStep1()) {
            event.preventDefault();
            return;
        }
        persistStep1Fields();
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();
            dropzone.classList.add("product-form__dropzone--dragover");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();
            dropzone.classList.remove("product-form__dropzone--dragover");
        });
    });

    dropzone.addEventListener("drop", (event) => {
        const files = event.dataTransfer?.files;
        if (files && files.length) {
            addFiles(files);
        }
    });

    restoreStep1Fields();
    updateUnidadOptions();

    try {
        const raw = sessionStorage.getItem(STEP1_STORAGE_KEY);
        if (raw) {
            const saved = JSON.parse(raw);
            if (unidadSelect && !unidadSelect.value && saved.unidad) {
                unidadSelect.value = saved.unidad;
            }
        }
    } catch (error) {
        console.warn("No se pudo restaurar la unidad del paso 1 del producto.", error);
    }

    if (tipoSelect?.value === "Otros" && tipoOtroGroup) {
        tipoOtroGroup.style.display = "flex";
    }

    updateCounter();
});
