document.addEventListener("DOMContentLoaded", function () {
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
    const cantidadInput = document.getElementById("cantidad-producto");
    const nextStepButton = document.getElementById("btn-next-step-producto");

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

        const nombre = (nombreInput?.value || "").trim();
        if (!nombre) {
            setError("error-nombre-producto", "El nombre del producto es obligatorio.");
            hasErrors = true;
        } else if (nombre.length < 3) {
            setError("error-nombre-producto", "El nombre debe tener al menos 3 caracteres.");
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

        const cantidadRaw = (cantidadInput?.value || "").trim();
        const cantidad = Number(cantidadRaw);
        if (!cantidadRaw) {
            setError("error-cantidad-producto", "La cantidad es obligatoria.");
            hasErrors = true;
        } else if (!Number.isInteger(cantidad) || cantidad <= 0) {
            setError("error-cantidad-producto", "Ingresa una cantidad válida mayor que 0.");
            hasErrors = true;
        } else {
            setError("error-cantidad-producto", "");
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
        counter.textContent = `${selectedFiles.length}/${maxFotos} fotos cargadas`;
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
            if (!exists && selectedFiles.length < maxFotos) {
                selectedFiles.push(file);
            }
        });

        syncInputFiles();
        updateCounter();
        renderPreview();
    };

    input.addEventListener("change", () => {
        addFiles(input.files);
    });

    [nombreInput, tipoSelect, cantidadInput].forEach((field) => {
        field?.addEventListener("input", validateStep1);
        field?.addEventListener("change", validateStep1);
    });

    nextStepButton?.addEventListener("click", (event) => {
        if (!validateStep1()) {
            event.preventDefault();
        }
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

    updateCounter();
});
