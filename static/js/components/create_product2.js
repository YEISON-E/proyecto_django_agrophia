document.addEventListener("DOMContentLoaded", function () {
    const STEP1_STORAGE_KEY = "agrophia.create_product.step1";
    const STEP2_STORAGE_KEY = "agrophia.create_product.step2";
    const successFlash = document.getElementById("flash-product-created");

    if (successFlash) {
        sessionStorage.removeItem(STEP1_STORAGE_KEY);
        sessionStorage.removeItem(STEP2_STORAGE_KEY);
        return;
    }

    const precioInput = document.getElementById("precio-producto");
    const stockInput = document.getElementById("stock-producto");
    const descripcionInput = document.getElementById("descripcion-producto");
    const garantiaInput = document.getElementById("garantia-producto");
    const publicarButton = document.getElementById("btn-publicar-producto");
    const step2Form = document.getElementById("create-product-step2-form");

    if (!precioInput || !stockInput || !descripcionInput || !garantiaInput || !publicarButton) {
        return;
    }

    const persistStep2Fields = () => {
        try {
            const payload = {
                precio: precioInput.value || "",
                stock: stockInput.value || "",
                descripcion: descripcionInput.value || "",
                garantia: garantiaInput.value || "",
            };
            sessionStorage.setItem(STEP2_STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
            console.warn("No se pudo guardar el paso 2 del producto en sessionStorage.", error);
        }
    };

    const restoreStep2Fields = () => {
        try {
            const raw = sessionStorage.getItem(STEP2_STORAGE_KEY);
            if (!raw) {
                return;
            }
            const saved = JSON.parse(raw);
            if (!precioInput.value && saved.precio) {
                precioInput.value = saved.precio;
            }
            if (!stockInput.value && saved.stock) {
                stockInput.value = saved.stock;
            }
            if (!descripcionInput.value && saved.descripcion) {
                descripcionInput.value = saved.descripcion;
            }
            if (!garantiaInput.value && saved.garantia) {
                garantiaInput.value = saved.garantia;
            }
        } catch (error) {
            console.warn("No se pudo restaurar el paso 2 del producto desde sessionStorage.", error);
        }
    };

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

    const validateStep2 = () => {
        let hasErrors = false;
        const garantiaPattern = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s.,:/%\-]+$/;

        const precioRaw = (precioInput.value || "").trim();
        const precio = Number(precioRaw);
        if (!precioRaw) {
            setError("error-precio-producto", "El precio es obligatorio.");
            hasErrors = true;
        } else if (Number.isNaN(precio) || precio <= 0) {
            setError("error-precio-producto", "Ingresa un precio válido mayor que 0.");
            hasErrors = true;
        } else {
            setError("error-precio-producto", "");
        }

        const stockRaw = (stockInput.value || "").trim();
        const stock = Number.parseInt(stockRaw, 10);
        if (!stockRaw) {
            setError("error-stock-producto", "La cantidad disponible es obligatoria.");
            hasErrors = true;
        } else if (!Number.isInteger(stock) || stock < 1) {
            setError("error-stock-producto", "La cantidad disponible debe ser al menos 1.");
            hasErrors = true;
        } else {
            setError("error-stock-producto", "");
        }

        const descripcion = (descripcionInput.value || "").trim();
        if (!descripcion) {
            setError("error-descripcion-producto", "La descripción es obligatoria.");
            hasErrors = true;
        } else if (descripcion.length < 10) {
            setError("error-descripcion-producto", "La descripción debe tener al menos 10 caracteres.");
            hasErrors = true;
        } else if (descripcion.length > 255) {
            setError("error-descripcion-producto", "La descripción no debe superar 255 caracteres.");
            hasErrors = true;
        } else {
            setError("error-descripcion-producto", "");
        }

        const garantia = (garantiaInput.value || "").trim();
        if (!garantia) {
            setError("error-garantia-producto", "El tiempo de durabilidad es obligatorio.");
            hasErrors = true;
        } else if (garantia.length < 3) {
            setError("error-garantia-producto", "El tiempo de durabilidad debe tener al menos 3 caracteres.");
            hasErrors = true;
        } else if (garantia.length > 120) {
            setError("error-garantia-producto", "La garantía no debe superar 120 caracteres.");
            hasErrors = true;
        } else if (!garantiaPattern.test(garantia)) {
            setError("error-garantia-producto", "La garantía contiene caracteres no permitidos.");
            hasErrors = true;
        } else {
            setError("error-garantia-producto", "");
        }

        return !hasErrors;
    };

    [precioInput, stockInput, descripcionInput, garantiaInput].forEach((field) => {
        field.addEventListener("input", validateStep2);
        field.addEventListener("change", validateStep2);
        field.addEventListener("input", persistStep2Fields);
        field.addEventListener("change", persistStep2Fields);
    });

    publicarButton.addEventListener("click", (event) => {
        if (!validateStep2()) {
            event.preventDefault();
        }
    });

    step2Form?.addEventListener("submit", (event) => {
        if (!validateStep2()) {
            event.preventDefault();
            return;
        }
        persistStep2Fields();
    });

    restoreStep2Fields();
    validateStep2();
});
