// JS para crear producto admin (puedes agregar validaciones y lógica de UI aquí)
document.addEventListener('DOMContentLoaded', function() {
  const tipoSelect = document.getElementById('tipo');
  const tipoOtroGroup = document.getElementById('group-tipo-otro');
  if (tipoSelect && tipoOtroGroup) {
    tipoSelect.addEventListener('change', function() {
      if (this.value === 'Otros') {
        tipoOtroGroup.style.display = 'block';
      } else {
        tipoOtroGroup.style.display = 'none';
      }
    });
  }
});
