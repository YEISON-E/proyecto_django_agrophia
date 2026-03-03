document.addEventListener("DOMContentLoaded", function () {
    const payButton = document.getElementById("cart-pay-btn");
    const paymentMethod = document.querySelector("select[name='payment-method']");
    const shippingMethod = document.querySelector("select[name='shipping-method']");
    const quantityInputs = Array.from(document.querySelectorAll(".cart__input"));

    if (!payButton) {
        return;
    }

    const showTemporaryAlert = (message, isError = false) => {
        const previous = document.getElementById("cart-temporary-alert");
        if (previous) {
            previous.remove();
        }

        const alertBox = document.createElement("div");
        alertBox.id = "cart-temporary-alert";
        alertBox.className = `cart-feedback__alert ${isError ? "cart-feedback__alert--error" : "cart-feedback__alert--success"}`;
        alertBox.textContent = message;

        document.body.appendChild(alertBox);
        window.setTimeout(() => {
            alertBox.remove();
        }, 1500);
    };

    quantityInputs.forEach((input) => {
        input.addEventListener("input", () => {
            const parsed = Number.parseInt(input.value, 10);
            if (Number.isNaN(parsed) || parsed < 1) {
                input.value = "1";
            }
        });
    });

    payButton.addEventListener("click", function (event) {
        event.preventDefault();

        if (!paymentMethod || !paymentMethod.value) {
            showTemporaryAlert("Selecciona un método de pago.", true);
            paymentMethod?.focus();
            return;
        }

        if (!shippingMethod || !shippingMethod.value) {
            showTemporaryAlert("Selecciona un método de envío.", true);
            shippingMethod?.focus();
            return;
        }

        const hasInvalidQuantity = quantityInputs.some((input) => {
            const parsed = Number.parseInt(input.value, 10);
            return Number.isNaN(parsed) || parsed < 1;
        });

        if (hasInvalidQuantity) {
            showTemporaryAlert("Hay cantidades inválidas en el carrito.", true);
            quantityInputs[0]?.focus();
            return;
        }

        showTemporaryAlert("¡Compra exitosa!");
        window.setTimeout(() => {
            window.location.href = payButton.href;
        }, 1500);
    });
});