document.addEventListener("DOMContentLoaded", function () {
    const precioInput = document.getElementById("precio-producto");
    const stockInput = document.getElementById("stock-producto");
    const descripcionInput = document.getElementById("descripcion-producto");
    const garantiaInput = document.getElementById("garantia-producto");
    const publicarButton = document.getElementById("btn-publicar-producto");
    const step2Form = document.getElementById("create-product-step2-form");

    if (!precioInput || !stockInput || !descripcionInput || !garantiaInput || !publicarButton) {
        return;
    }

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
        } else if (!Number.isInteger(stock) || stock < 0) {
            setError("error-stock-producto", "Ingresa una cantidad disponible válida.");
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
        } else {
            setError("error-garantia-producto", "");
        }

        return !hasErrors;
    };

    [precioInput, stockInput, descripcionInput, garantiaInput].forEach((field) => {
        field.addEventListener("input", validateStep2);
        field.addEventListener("change", validateStep2);
    });

    publicarButton.addEventListener("click", (event) => {
        if (!validateStep2()) {
            event.preventDefault();
        }
    });

    step2Form?.addEventListener("submit", (event) => {
        if (!validateStep2()) {
            event.preventDefault();
        }
    });
});
