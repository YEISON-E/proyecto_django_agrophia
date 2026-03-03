document.addEventListener("DOMContentLoaded", function () {
    const payButton = document.getElementById("cart-pay-btn");
    if (!payButton) {
        return;
    }

    payButton.addEventListener("click", function (event) {
        event.preventDefault();
        alert("¡Compra exitosa!");
        window.location.href = payButton.href;
    });
});