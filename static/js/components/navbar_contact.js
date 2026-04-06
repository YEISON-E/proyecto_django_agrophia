// Espera a que el DOM esté cargado para inyectar y configurar el navbar.
document.addEventListener("DOMContentLoaded", function () {
  // Busca el contenedor donde se renderiza el navbar de contacto.
  const navbarElement = document.querySelector(".contact-home__container");

  // Solo continúa si el contenedor existe en la vista.
  if (navbarElement) {
    // Solicita el HTML del componente navbar de contacto.
    fetch("/frontend/public/views/components/navbar_contact.html")
      // Convierte la respuesta HTTP en texto.
      .then((response) => response.text())
      // Inserta el markup y enlaza eventos de interacción.
      .then((data) => {
        navbarElement.innerHTML = data;

        // Obtiene botón toggle del menú principal.
        const toggleBtn = navbarElement.querySelector(".navbar-home__toggle");
        // Obtiene lista principal de navegación.
        const navList = navbarElement.querySelector(".navbar-home__list");
        // Al hacer clic, alterna la visibilidad del menú principal.
        toggleBtn?.addEventListener("click", () => {
          navList.classList.toggle("show");
        });

        // Obtiene botón toggle del menú de usuario.
        const userToggle = navbarElement.querySelector(".user-menu__toggle");
        // Obtiene lista desplegable del usuario.
        const userMenu = navbarElement.querySelector(".user-menu__list");

        // Al hacer clic, alterna la visibilidad del menú de usuario.
        userToggle?.addEventListener("click", () => {
          userMenu.classList.toggle("show");
        });

        // Cierra ambos menús cuando el clic ocurre fuera del navbar.
        document.addEventListener("click", (e) => {
          if (!navbarElement.contains(e.target)) {
            userMenu?.classList.remove("show");
            navList?.classList.remove("show");
          }
        });
      })
      // Registra error de carga del componente en consola.
      .catch((error) => console.error("Error cargando el navbar", error));
  }
});