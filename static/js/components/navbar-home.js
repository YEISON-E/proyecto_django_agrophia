/*document.addEventListener("DOMContentLoaded", function(){
    const navbarElement = document.querySelector(".header-home__container");

    if(navbarElement){
        fetch("/frontend/public/views/components/navbar-home.html")
        .then(response => response.text())
        .then(data => {
            navbarElement.innerHTML = data;
            
            const navLinks = navbarElement.querySelectorAll(".navbar-home__link");
    })
    .catch(error => console.error("Error cargando el navbar", error));

    }
});*/

// Espera a que el DOM esté listo para inyectar y configurar el navbar principal.
document.addEventListener("DOMContentLoaded", function () {
  // Busca contenedor objetivo del navbar home.
  const navbarElement = document.querySelector(".header-home__container");

  // Solo ejecuta la carga si el contenedor existe.
  if (navbarElement) {
    // Solicita el HTML del componente navbar home.
    fetch("/frontend/public/views/components/navbar-home.html")
      // Convierte respuesta a texto HTML.
      .then((response) => response.text())
      // Inserta el markup y activa interacciones.
      .then((data) => {
        navbarElement.innerHTML = data;

        // Obtiene botón de menú principal.
        const toggleBtn = navbarElement.querySelector(".navbar-home__toggle");
        // Obtiene lista principal de navegación.
        const navList = navbarElement.querySelector(".navbar-home__list");
        // Alterna visibilidad del menú principal al hacer clic.
        toggleBtn?.addEventListener("click", () => {
          navList.classList.toggle("show");
        });

        // Obtiene botón del menú de usuario.
        const userToggle = navbarElement.querySelector(".user-menu__toggle");
        // Obtiene lista del menú de usuario.
        const userMenu = navbarElement.querySelector(".user-menu__list");

        // Alterna visibilidad del menú de usuario al hacer clic.
        userToggle?.addEventListener("click", () => {
          userMenu.classList.toggle("show");
        });

        // Cierra menús si se hace clic fuera del navbar.
        document.addEventListener("click", (e) => {
          if (!navbarElement.contains(e.target)) {
            userMenu?.classList.remove("show");
            navList?.classList.remove("show");
          }
        });
      })
      // Registra errores de carga del navbar.
      .catch((error) => console.error("Error cargando el navbar", error));
  }
});

