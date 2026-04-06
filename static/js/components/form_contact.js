// Espera a que el DOM esté completamente cargado antes de ejecutar la lógica.
document.addEventListener("DOMContentLoaded", function(){
    // Busca el contenedor donde se inyectará el formulario de contacto.
    const formElement = document.querySelector(".contact-form-container");

    // Solo continúa si el contenedor existe en la página actual.
    if(formElement){
        // Solicita el HTML del componente de formulario de contacto.
        fetch("/frontend/public/views/components/form_contact.html")
        // Convierte la respuesta HTTP a texto (markup HTML).
        .then(response => response.text())
        // Inserta el HTML recibido dentro del contenedor.
        .then(data => {
            formElement.innerHTML = data;
            
    })
    // Si ocurre un error en la carga, lo muestra en consola.
    .catch(error => console.error("Error cargando el formulario de contacto", error));

    }
});