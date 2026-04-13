// Espera a que el documento esté completamente cargado antes de inicializar.
document.addEventListener("DOMContentLoaded", function () {
    // Obtiene todos los formularios de activación de producto basados en data attribute.
    const forms = Array.from(document.querySelectorAll("[data-enable-product-form]"));
    // Obtiene el overlay de confirmación para activar producto.
    const overlay = document.getElementById("enable-product-overlay");
    // Obtiene el botón cancelar dentro del overlay de confirmación.
    const cancelButton = document.querySelector("[data-enable-product-cancel]");
    // Obtiene el botón confirmar dentro del overlay de confirmación.
    const confirmButton = document.querySelector("[data-enable-product-confirm]");
    // Obtiene el modal para enviar mensaje al administrador.
    const adminModal = document.getElementById("admin-reactivation-modal");
    // Obtiene el backdrop del modal de reactivación por administrador.
    const adminModalBackdrop = document.getElementById("admin-reactivation-backdrop");
    // Obtiene el botón de cierre del modal de reactivación.
    const adminModalClose = document.getElementById("close-admin-reactivation-modal");
    // Obtiene el formulario para enviar solicitud al administrador.
    const adminForm = document.getElementById("admin-reactivation-form");
    // Obtiene el textarea del mensaje al administrador.
    const adminTextarea = document.getElementById("admin-reactivation-text");
    // Obtiene el overlay de feedback para mostrar mensajes al usuario.
    const feedbackOverlay = document.getElementById("feedback-overlay");
    // Obtiene el elemento de texto del feedback.
    const feedbackMessage = document.getElementById("feedback-message");
    // Obtiene el botón de cierre del feedback.
    const feedbackClose = document.getElementById("feedback-close");

    // Función auxiliar para leer el valor de una cookie por nombre.
    const getCookie = function (name) {
        // Busca la cookie por nombre recorriendo el string de cookies del documento.
        const cookieValue = document.cookie
            .split(";")
            .map((cookie) => cookie.trim())
            .find((cookie) => cookie.startsWith(name + "="));
        // Devuelve el valor decodificado o una cadena vacía si no existe.
        return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
    };

    // Envía un formulario por fetch con CSRF y maneja diferentes tipos de respuesta.
    const submitFormWithCsrf = async function (form) {
        // Obtiene token CSRF desde cookies.
        const csrftoken = getCookie("csrftoken");
        // Crea cuerpo multipart con los datos actuales del formulario.
        const body = new FormData(form);

        // Realiza petición POST asíncrona a la acción del formulario.
        const response = await fetch(form.action, {
            // Define método HTTP.
            method: "POST",
            // Define headers para CSRF y solicitud AJAX.
            headers: {
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
            // Incluye el cuerpo con datos del formulario.
            body: body,
            // Mantiene credenciales de misma sesión/origen.
            credentials: "same-origin",
        });

        // Si el backend respondió con redirección, navega a la nueva URL.
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        // Lee tipo de contenido para saber si puede parsear JSON.
        const contentType = response.headers.get("content-type") || "";
        // Si viene JSON, devuelve el objeto parseado.
        if (contentType.includes("application/json")) {
            const data = await response.json();
            return data;
        }

        // Si no es respuesta exitosa y no fue JSON, lanza error genérico.
        if (!response.ok) {
            throw new Error("No se pudo procesar la solicitud.");
        }

        // Si fue exitoso sin JSON, recarga página para reflejar cambios.
        window.location.reload();
    };

    // Envía mensaje al administrador para solicitar reactivación.
    const postAdminMessage = async function (url, messageText) {
        // Obtiene token CSRF desde cookies.
        const csrftoken = getCookie("csrftoken");
        // Crea FormData para enviar el mensaje.
        const body = new FormData();
        // Agrega el campo message al cuerpo.
        body.append("message", messageText);

        // Realiza petición POST asíncrona al endpoint dado.
        const response = await fetch(url, {
            // Define método HTTP.
            method: "POST",
            // Define headers para CSRF y solicitud AJAX.
            headers: {
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest",
            },
            // Incluye cuerpo de la petición con el mensaje.
            body: body,
            // Mantiene credenciales en mismo origen.
            credentials: "same-origin",
        });

        // Parsea el cuerpo JSON de la respuesta.
        const data = await response.json();
        // Si HTTP o negocio fallan, lanza error con mensaje del backend.
        if (!response.ok || !data.ok) {
            throw new Error(data.message || "No se pudo enviar la solicitud.");
        }
        // Retorna datos cuando la operación fue exitosa.
        return data;
    };

    // Muestra feedback visual con mensaje al usuario.
    const showFeedback = function (messageText) {
        // Si faltan elementos de feedback, no hace nada.
        if (!feedbackOverlay || !feedbackMessage) {
            return;
        }

        // Inserta el texto del feedback en pantalla.
        feedbackMessage.textContent = messageText;
        // Quita estado de cierre por si venía de una transición previa.
        feedbackOverlay.classList.remove("profile-shop-alert-overlay--closing");
        // Activa estado abierto del overlay de feedback.
        feedbackOverlay.classList.add("profile-shop-alert-overlay--open");
        // Actualiza atributo de accesibilidad indicando que está visible.
        feedbackOverlay.setAttribute("aria-hidden", "false");
    };

    // Cierra el feedback con transición CSS.
    const closeFeedback = function () {
        // Si no existe overlay o no está abierto, no hay nada que cerrar.
        if (!feedbackOverlay || !feedbackOverlay.classList.contains("profile-shop-alert-overlay--open")) {
            return;
        }

        // Activa estado visual de cierre.
        feedbackOverlay.classList.add("profile-shop-alert-overlay--closing");
        // Marca overlay como oculto para accesibilidad.
        feedbackOverlay.setAttribute("aria-hidden", "true");

        // Espera a que termine animación para limpiar clases de estado.
        window.setTimeout(function () {
            feedbackOverlay.classList.remove("profile-shop-alert-overlay--open", "profile-shop-alert-overlay--closing");
        }, 180);
    };

    // Si faltan elementos críticos para el flujo principal, detiene inicialización.
    if (!forms.length || !overlay || !cancelButton || !confirmButton) {
        return;
    }

    // Guarda formulario pendiente de confirmación para enviarlo luego.
    let pendingForm = null;
    // Guarda URL pendiente para solicitud de reactivación al administrador.
    let pendingAdminRequestUrl = "";

    // Abre overlay de confirmación y asigna el formulario en espera.
    const openOverlay = function (form) {
        // Guarda referencia del formulario seleccionado.
        pendingForm = form;
        // Limpia clase de cierre para evitar conflicto de estados.
        overlay.classList.remove("profile-shop-alert-overlay--closing");
        // Activa estado abierto del overlay.
        overlay.classList.add("profile-shop-alert-overlay--open");
        // Marca overlay como visible para accesibilidad.
        overlay.setAttribute("aria-hidden", "false");
    };

    // Cierra overlay de confirmación y limpia formulario pendiente.
    const closeOverlay = function () {
        // Si ya no está abierto, solo limpia estado interno y sale.
        if (!overlay.classList.contains("profile-shop-alert-overlay--open")) {
            pendingForm = null;
            return;
        }

        // Activa clase visual de cierre para transición.
        overlay.classList.add("profile-shop-alert-overlay--closing");
        // Marca overlay como oculto para accesibilidad.
        overlay.setAttribute("aria-hidden", "true");

        // Espera fin de transición y limpia clases + estado interno.
        window.setTimeout(function () {
            overlay.classList.remove("profile-shop-alert-overlay--open", "profile-shop-alert-overlay--closing");
            pendingForm = null;
        }, 180);
    };

    // Abre modal de solicitud al administrador usando URL de destino.
    const openAdminModal = function (requestUrl) {
        // Guarda URL pendiente para usarla al enviar el formulario del modal.
        pendingAdminRequestUrl = requestUrl;
        // Si existe textarea, lo limpia para empezar con mensaje vacío.
        if (adminTextarea) {
            adminTextarea.value = "";
        }
        // Muestra modal agregando clase de abierto.
        adminModal.classList.add("seller-message-modal--open");
        // Actualiza atributo de accesibilidad indicando visibilidad.
        adminModal.setAttribute("aria-hidden", "false");
    };

    // Cierra modal de administrador y limpia URL pendiente.
    const closeAdminModal = function () {
        // Reinicia URL pendiente de solicitud.
        pendingAdminRequestUrl = "";
        // Oculta modal removiendo clase de abierto.
        adminModal.classList.remove("seller-message-modal--open");
        // Marca modal como oculto para accesibilidad.
        adminModal.setAttribute("aria-hidden", "true");
    };

    // Recorre todos los formularios y reemplaza submit por confirmación en overlay.
    forms.forEach(function (form) {
        // Intercepta envío del formulario de activación.
        form.addEventListener("submit", function (event) {
            // Evita submit inmediato para pedir confirmación al usuario.
            event.preventDefault();
            // Abre overlay de confirmación para este formulario.
            openOverlay(form);
        });
    });

    // Cierra overlay al pulsar botón cancelar.
    cancelButton.addEventListener("click", function () {
        closeOverlay();
    });

    // Maneja confirmación para enviar formulario pendiente.
    confirmButton.addEventListener("click", async function () {
        // Si no hay formulario pendiente, no continúa.
        if (!pendingForm) {
            return;
        }

        // Deshabilita botón para evitar doble clic durante petición.
        confirmButton.disabled = true;
        try {
            // Envía formulario con CSRF y espera resultado del backend.
            const result = await submitFormWithCsrf(pendingForm);
            // Si backend exige mensaje al administrador, informa al usuario.
            if (result && result.requires_admin_message) {
                showFeedback("Este producto fue deshabilitado por el administrador; si desea activarlo, por favor envíe un mensaje al administrador.");
                // Obtiene URL de solicitud desde data attribute del formulario.
                const requestUrl = pendingForm.dataset.requestUrl || "";
                // Si hay URL y modal disponible, abre flujo de solicitud al admin.
                if (requestUrl && adminModal && adminForm) {
                    closeOverlay();
                    openAdminModal(requestUrl);
                    return;
                }
            }
        } catch (error) {
            // Muestra error genérico si falla activación.
            showFeedback("No se pudo completar la acción. Recarga la página e intenta de nuevo.");
        } finally {
            // Rehabilita botón confirmar al finalizar intento.
            confirmButton.disabled = false;
            // Cierra overlay de confirmación.
            closeOverlay();
        }
    });

    // Si están todos los nodos del modal admin, inicializa sus eventos.
    if (adminForm && adminModal && adminModalClose && adminModalBackdrop && adminTextarea) {
        // Cierra modal al pulsar botón de cierre.
        adminModalClose.addEventListener("click", closeAdminModal);
        // Cierra modal al hacer clic sobre el backdrop.
        adminModalBackdrop.addEventListener("click", closeAdminModal);

        // Intercepta submit del formulario de solicitud al administrador.
        adminForm.addEventListener("submit", async function (event) {
            // Evita submit tradicional con recarga de página.
            event.preventDefault();
            // Lee y limpia el texto ingresado por el usuario.
            const messageText = (adminTextarea.value || "").trim();
            // Si no hay URL pendiente, no puede enviar solicitud.
            if (!pendingAdminRequestUrl) {
                return;
            }

            // Busca botón submit del formulario para bloquearlo temporalmente.
            const submitButton = adminForm.querySelector("button[type='submit']");
            // Si existe, lo deshabilita durante la petición.
            if (submitButton) {
                submitButton.disabled = true;
            }

            try {
                // Envía mensaje al administrador y espera confirmación.
                const data = await postAdminMessage(pendingAdminRequestUrl, messageText);
                // Muestra mensaje de éxito devuelto por backend o fallback.
                showFeedback(data.message || "Tu solicitud fue enviada al administrador.");
                // Cierra modal al completar envío exitoso.
                closeAdminModal();
            } catch (error) {
                // Muestra error recibido o mensaje genérico.
                showFeedback(error.message || "No se pudo enviar el mensaje al administrador.");
            } finally {
                // Vuelve a habilitar botón submit al terminar.
                if (submitButton) {
                    submitButton.disabled = false;
                }
            }
        });
    }

    // Si existe botón de cierre del feedback, asigna su manejador.
    if (feedbackClose) {
        feedbackClose.addEventListener("click", closeFeedback);
    }

    // Si existe overlay de feedback, permite cerrar haciendo clic fuera del contenido.
    if (feedbackOverlay) {
        feedbackOverlay.addEventListener("click", function (event) {
            // Cierra solo cuando el clic es sobre el overlay mismo.
            if (event.target === feedbackOverlay) {
                closeFeedback();
            }
        });
    }

    // Permite cerrar overlay de confirmación al hacer clic fuera del cuadro.
    overlay.addEventListener("click", function (event) {
        // Cierra solo cuando el clic es sobre el overlay.
        if (event.target === overlay) {
            closeOverlay();
        }
    });

    // Maneja tecla Escape para cerrar overlays/modales abiertos.
    document.addEventListener("keydown", function (event) {
        // Si Escape y overlay principal abierto, lo cierra.
        if (event.key === "Escape" && overlay.classList.contains("profile-shop-alert-overlay--open")) {
            closeOverlay();
        }

        // Si Escape y modal admin abierto, lo cierra.
        if (event.key === "Escape" && adminModal && adminModal.classList.contains("seller-message-modal--open")) {
            closeAdminModal();
        }

        // Si Escape y feedback abierto, lo cierra.
        if (event.key === "Escape" && feedbackOverlay && feedbackOverlay.classList.contains("profile-shop-alert-overlay--open")) {
            closeFeedback();
        }
    });
});
