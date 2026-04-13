// Espera a que el DOM esté cargado antes de renderizar el listado de inicio.
document.addEventListener("DOMContentLoaded", function(){
    // Busca contenedor donde se insertará el componente list-home.
    const navbarElement = document.querySelector(".list-home__container");

    // Solo ejecuta la carga si existe el contenedor objetivo.
    if(navbarElement){
        // Solicita el HTML del componente de lista.
        fetch("/frontend/public/views/components/list-home.html")
        // Convierte la respuesta HTTP a texto.
        .then(response => response.text())
        // Inyecta el HTML resultante en el contenedor.
        .then(data => {
            navbarElement.innerHTML = data;
    })
    // Si falla la petición, muestra error en consola.
    .catch(error => console.error("Error cargando la lista", error));

    }
});