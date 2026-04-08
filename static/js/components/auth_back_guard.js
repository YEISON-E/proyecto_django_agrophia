// Espera a que el documento HTML termine de cargar por completo.
document.addEventListener("DOMContentLoaded", function () {
  // Escucha el evento pageshow, que se dispara al mostrarse una pagina.
  window.addEventListener("pageshow", function (event) {
    // Obtiene entradas de navegacion del Performance API.
    const navEntries = performance.getEntriesByType("navigation");
    // Determina el tipo de navegacion; usa cadena vacia si no hay datos.
    const navType = navEntries && navEntries.length ? navEntries[0].type : "";

    // Si la pagina proviene de cache back/forward, fuerza recarga para revalidar autenticacion.
    if (event.persisted || navType === "back_forward") {
      // Recarga la pagina para ejecutar nuevamente validaciones del servidor.
      window.location.reload();
    }
  });
});
