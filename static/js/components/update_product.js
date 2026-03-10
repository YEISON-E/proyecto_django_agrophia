document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("update-product-form");
    const input = document.getElementById("update-input-fotos");
    const dropzone = document.getElementById("update-dropzone-fotos");
    const previewGrid = document.getElementById("update-fotos-preview");
    const counter = document.getElementById("update-fotos-counter");

    if (!form || !input || !dropzone || !previewGrid || !counter) {
        return;
    }

    const maxFotos = Number(form.dataset.maxImages || 8);
    const initialExisting = Number(form.dataset.existingImages || 0);
    let selectedFiles = [];

    const deleteInputs = Array.from(form.querySelectorAll("[data-delete-image-input]"));
    const deleteButtons = Array.from(form.querySelectorAll("[data-delete-image-button]"));

    const currentDeleteCount = () => deleteInputs.filter((inputEl) => inputEl.checked).length;
    const existingAfterDelete = () => initialExisting - currentDeleteCount();

    const syncInputFiles = () => {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach((file) => dataTransfer.items.add(file));
        input.files = dataTransfer.files;
    };

    const updateCounter = () => {
        const existingCount = existingAfterDelete();
        const total = existingCount + selectedFiles.length;
        counter.textContent = `${selectedFiles.length} nuevas | ${existingCount}/8 actuales | total ${total}/8`;

        const canUploadMore = total < maxFotos;
        // If there are already selected files, keep input enabled so they are submitted with the form.
        input.disabled = !canUploadMore && selectedFiles.length === 0;
        dropzone.style.opacity = canUploadMore ? "1" : "0.7";
    };

    const renderPreview = () => {
        previewGrid.innerHTML = "";

        selectedFiles.forEach((file, index) => {
            const card = document.createElement("div");
            card.className = "product-form__preview-item";

            const image = document.createElement("img");
            image.className = "product-form__preview-image";
            image.alt = `Nueva foto ${index + 1}`;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "product-form__preview-remove";
            removeButton.textContent = "x";

            removeButton.addEventListener("click", () => {
                selectedFiles.splice(index, 1);
                syncInputFiles();
                renderPreview();
                updateCounter();
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
        const allowedSlots = maxFotos - existingAfterDelete() - selectedFiles.length;
        if (allowedSlots <= 0) {
            return;
        }

        const incoming = Array.from(fileList)
            .filter((file) => (file.type || "").startsWith("image/"))
            .slice(0, allowedSlots);

        selectedFiles = selectedFiles.concat(incoming);
        syncInputFiles();
        renderPreview();
        updateCounter();
    };

    input.addEventListener("change", function () {
        addFiles(input.files);
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

    deleteButtons.forEach((button, index) => {
        button.addEventListener("click", function () {
            const checkbox = deleteInputs[index];
            const item = button.closest("[data-existing-image-item]");
            if (!checkbox || !item) {
                return;
            }

            checkbox.checked = !checkbox.checked;
            item.classList.toggle("product-form__preview-item--selected", checkbox.checked);
            updateCounter();
        });
    });

    updateCounter();
});