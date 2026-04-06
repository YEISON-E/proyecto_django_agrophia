// Script de apoyo para formulario de creación de producto en admin.
// Espera la carga completa del DOM.
document.addEventListener('DOMContentLoaded', function() {
  // Obtiene select del tipo de producto.
  const tipoSelect = document.getElementById('tipo');
  // Obtiene contenedor del campo "otro tipo".
  const tipoOtroGroup = document.getElementById('group-tipo-otro');
  // Solo registra eventos si ambos elementos existen.
  if (tipoSelect && tipoOtroGroup) {
    // Al cambiar el tipo, muestra u oculta campo adicional.
    tipoSelect.addEventListener('change', function() {
      // Si selecciona "Otros", muestra el campo extra.
      if (this.value === 'Otros') {
        tipoOtroGroup.style.display = 'block';
      } else {
        // Para cualquier otro valor, oculta el campo extra.
        tipoOtroGroup.style.display = 'none';
      }
    });
  }
});
