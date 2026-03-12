document.addEventListener("DOMContentLoaded", function () {
    const printButton = document.getElementById("print-order");
    const copyButton = document.getElementById("copy-order-id");
    const detailCard = document.querySelector("[data-order-number]");
    const toast = document.getElementById("order-detail-toast");

    const showToast = function (message) {
        if (!toast) {
            return;
        }

        toast.textContent = message;
        toast.classList.add("order-detail__toast--show");
        window.setTimeout(function () {
            toast.classList.remove("order-detail__toast--show");
        }, 1800);
    };

    if (printButton) {
        printButton.addEventListener("click", function () {
            window.print();
        });
    }

    if (copyButton && detailCard) {
        copyButton.addEventListener("click", async function () {
            const orderNumber = detailCard.dataset.orderNumber || "";
            if (!orderNumber) {
                return;
            }

            try {
                await navigator.clipboard.writeText(orderNumber);
                showToast("Numero de pedido copiado");
            } catch (error) {
                showToast("No se pudo copiar");
            }
        });
    }
});
