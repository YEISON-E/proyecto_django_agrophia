// Espera a que el DOM esté listo para montar el componente de buscador.
document.addEventListener("DOMContentLoaded", function () {
    // Busca contenedor objetivo del buscador en la vista.
    const searchContainer = document.querySelector(".search__container-index");
  
    // Solo carga el componente si el contenedor existe.
    if (searchContainer) {
      // Solicita el HTML del componente search.
      fetch("/frontend/public/views/components/search.html")
        // Convierte la respuesta HTTP a texto.
        .then(response => response.text())
        // Inserta el markup en el contenedor del buscador.
        .then(data => {
          searchContainer.innerHTML = data;
        })
        // Reporta cualquier fallo de carga en consola.
        .catch(error => console.error("Error cargando el buscador:", error));
    }
  });
  