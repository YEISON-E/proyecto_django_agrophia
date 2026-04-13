// Espera a que el DOM esté listo para cargar el componente visual del hero.
document.addEventListener("DOMContentLoaded", function(){
    // Busca contenedor donde se inyectará el hero de recuperación.
    const heroElement = document.querySelector(".forgot-password__hero-container");

    // Solo continúa si el contenedor existe en la página.
    if(heroElement){
        // Solicita el HTML del componente hero.
        fetch("/frontend/public/views/components/hero-forgot-password.html")
        // Convierte respuesta a texto HTML.
        .then(response => response.text())
        // Inserta el HTML recibido en el contenedor.
        .then(data =>{
            heroElement.innerHTML = data;
        })

    // Reporta en consola cualquier error de carga.
    .catch(error => console.log("Error cargando el hero", error));
    }
});