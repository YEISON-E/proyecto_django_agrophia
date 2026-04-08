document.addEventListener("DOMContentLoaded", function () {
    const printButton = document.getElementById("print-order");

    if (printButton) {
        printButton.addEventListener("click", function () {
            window.print();
        });
    }
});
