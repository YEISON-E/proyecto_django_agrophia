// Espera a que el DOM este listo para inicializar validaciones del paso 2.
document.addEventListener("DOMContentLoaded", function () {
    // Clave de sessionStorage para datos del paso 1.
    const STEP1_STORAGE_KEY = "agrophia.create_product.step1";
    // Clave de sessionStorage para datos del paso 2.
    const STEP2_STORAGE_KEY = "agrophia.create_product.step2";
    // Nodo flash que indica creacion exitosa del producto.
    const successFlash = document.getElementById("flash-product-created");

    // Si hay mensaje de exito, limpia datos de pasos y termina.
    if (successFlash) {
        sessionStorage.removeItem(STEP1_STORAGE_KEY);
        sessionStorage.removeItem(STEP2_STORAGE_KEY);
        return;
    }

    // Input de precio del producto.
    const precioInput = document.getElementById("precio-producto");
    // Input de stock/cantidad disponible.
    const stockInput = document.getElementById("stock-producto");
    // Textarea/input de descripcion del producto.
    const descripcionInput = document.getElementById("descripcion-producto");
    // Input de tiempo de durabilidad.
    const tiempoDurabilidadInput = document.getElementById("tiempo-durabilidad-producto");
    // Boton para publicar producto.
    const publicarButton = document.getElementById("btn-publicar-producto");
    // Formulario del paso 2.
    const step2Form = document.getElementById("create-product-step2-form");

    // Si falta algun elemento critico, no continua inicializacion.
    if (!precioInput || !stockInput || !descripcionInput || !tiempoDurabilidadInput || !publicarButton) {
        return;
    }

    // Persiste campos del paso 2 en sessionStorage.
    const persistStep2Fields = () => {
        try {
            // Construye payload con valores actuales del formulario.
            const payload = {
                precio: precioInput.value || "",
                stock: stockInput.value || "",
                descripcion: descripcionInput.value || "",
                tiempo_durabilidad: tiempoDurabilidadInput.value || "",
            };
            // Guarda payload serializado.
            sessionStorage.setItem(STEP2_STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
            // Registra advertencia si falla el guardado.
            console.warn("No se pudo guardar el paso 2 del producto en sessionStorage.", error);
        }
    };

    // Restaura campos del paso 2 desde sessionStorage.
    const restoreStep2Fields = () => {
        try {
            // Lee valor guardado bruto.
            const raw = sessionStorage.getItem(STEP2_STORAGE_KEY);
            // Si no hay datos guardados, sale.
            if (!raw) {
                return;
            }
            // Parsea JSON guardado.
            const saved = JSON.parse(raw);
            // Restaura precio si campo actual esta vacio.
            if (!precioInput.value && saved.precio) {
                precioInput.value = saved.precio;
            }
            // Restaura stock si campo actual esta vacio.
            if (!stockInput.value && saved.stock) {
                stockInput.value = saved.stock;
            }
            // Restaura descripcion si campo actual esta vacio.
            if (!descripcionInput.value && saved.descripcion) {
                descripcionInput.value = saved.descripcion;
            }
            // Restaura tiempo de durabilidad si campo actual esta vacio.
            if (!tiempoDurabilidadInput.value && saved.tiempo_durabilidad) {
                tiempoDurabilidadInput.value = saved.tiempo_durabilidad;
            }
        } catch (error) {
            // Registra advertencia si falla restauracion.
            console.warn("No se pudo restaurar el paso 2 del producto desde sessionStorage.", error);
        }
    };

    // Helper para mostrar/ocultar mensajes de error por id.
    const setError = (id, message) => {
        // Busca nodo de error.
        const el = document.getElementById(id);
        // Si no existe nodo, finaliza.
        if (!el) {
            return;
        }
        // Si hay mensaje, lo muestra en pantalla.
        if (message) {
            el.textContent = message;
            el.style.display = "block";
        } else {
            // Si no hay mensaje, limpia y oculta el error.
            el.textContent = "";
            el.style.display = "none";
        }
    };

    // Valida todos los campos del paso 2.
    const validateStep2 = () => {
        // Bandera acumuladora de errores.
        let hasErrors = false;
        // Patron permitido para tiempo de durabilidad.
        const tiempoDurabilidadPattern = /^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s.,:/%\-]+$/;

        // Lee y normaliza precio.
        const precioRaw = (precioInput.value || "").trim();
        // Convierte precio a numero.
        const precio = Number(precioRaw);
        // Regla: precio obligatorio.
        if (!precioRaw) {
            setError("error-precio-producto", "El precio es obligatorio.");
            hasErrors = true;
        // Regla: precio numerico y mayor a cero.
        } else if (Number.isNaN(precio) || precio <= 0) {
            setError("error-precio-producto", "Ingresa un precio válido mayor que 0.");
            hasErrors = true;
        } else {
            // Limpia error de precio si es valido.
            setError("error-precio-producto", "");
        }

        // Lee y normaliza stock.
        const stockRaw = (stockInput.value || "").trim();
        // Convierte stock a entero base 10.
        const stock = Number.parseInt(stockRaw, 10);
        // Regla: stock obligatorio.
        if (!stockRaw) {
            setError("error-stock-producto", "La cantidad disponible es obligatoria.");
            hasErrors = true;
        // Regla: stock entero y minimo 1.
        } else if (!Number.isInteger(stock) || stock < 1) {
            setError("error-stock-producto", "La cantidad disponible debe ser al menos 1.");
            hasErrors = true;
        } else {
            // Limpia error de stock si es valido.
            setError("error-stock-producto", "");
        }

        // Lee y normaliza descripcion.
        const descripcion = (descripcionInput.value || "").trim();
        // Regla: descripcion obligatoria.
        if (!descripcion) {
            setError("error-descripcion-producto", "La descripción es obligatoria.");
            hasErrors = true;
        // Regla: minimo 10 caracteres.
        } else if (descripcion.length < 10) {
            setError("error-descripcion-producto", "La descripción debe tener al menos 10 caracteres.");
            hasErrors = true;
        // Regla: maximo 255 caracteres.
        } else if (descripcion.length > 255) {
            setError("error-descripcion-producto", "La descripción no debe superar 255 caracteres.");
            hasErrors = true;
        } else {
            // Limpia error de descripcion si es valida.
            setError("error-descripcion-producto", "");
        }

        // Lee y normaliza tiempo de durabilidad.
        const tiempoDurabilidad = (tiempoDurabilidadInput.value || "").trim();
        // Regla: tiempo de durabilidad obligatorio.
        if (!tiempoDurabilidad) {
            setError("error-tiempo-durabilidad-producto", "El tiempo de durabilidad es obligatorio.");
            hasErrors = true;
        // Regla: minimo 3 caracteres.
        } else if (tiempoDurabilidad.length < 3) {
            setError("error-tiempo-durabilidad-producto", "El tiempo de durabilidad debe tener al menos 3 caracteres.");
            hasErrors = true;
        // Regla: maximo 120 caracteres.
        } else if (tiempoDurabilidad.length > 120) {
            setError("error-tiempo-durabilidad-producto", "El tiempo de durabilidad no debe superar 120 caracteres.");
            hasErrors = true;
        // Regla: solo caracteres permitidos por patron.
        } else if (!tiempoDurabilidadPattern.test(tiempoDurabilidad)) {
            setError("error-tiempo-durabilidad-producto", "El tiempo de durabilidad contiene caracteres no permitidos.");
            hasErrors = true;
        } else {
            // Limpia error de tiempo de durabilidad si es valido.
            setError("error-tiempo-durabilidad-producto", "");
        }

        // Devuelve true solo si no hubo errores.
        return !hasErrors;
    };

    // Enlaza validacion y persistencia a eventos input/change de campos.
    [precioInput, stockInput, descripcionInput, tiempoDurabilidadInput].forEach((field) => {
        field.addEventListener("input", validateStep2);
        field.addEventListener("change", validateStep2);
        field.addEventListener("input", persistStep2Fields);
        field.addEventListener("change", persistStep2Fields);
    });

    // Evita accion del boton publicar cuando hay errores.
    publicarButton.addEventListener("click", (event) => {
        if (!validateStep2()) {
            event.preventDefault();
        }
    });

    // En submit, vuelve a validar y persiste si todo esta correcto.
    step2Form?.addEventListener("submit", (event) => {
        if (!validateStep2()) {
            event.preventDefault();
            return;
        }
        persistStep2Fields();
    });

    // Restaura valores guardados del paso 2.
    restoreStep2Fields();
    // Ejecuta validacion inicial para mostrar estado correcto al cargar.
    validateStep2();
});
