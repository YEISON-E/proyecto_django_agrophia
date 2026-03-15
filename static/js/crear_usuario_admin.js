// JS para selects dinámicos de departamento y municipio en crear usuario admin
window.addEventListener('DOMContentLoaded', function() {
  const departamentosMunicipios = window.departamentosMunicipiosData || {};
  const departamentoSelect = document.getElementById('departamento');
  const municipioSelect = document.getElementById('municipio');
  if (!departamentoSelect || !municipioSelect) return;

  function cargarMunicipios(dep, selectedMun) {
    municipioSelect.innerHTML = '<option value="">Seleccione...</option>';
    if (departamentosMunicipios[dep]) {
      departamentosMunicipios[dep].forEach(function(m) {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        if (m === selectedMun) opt.selected = true;
        municipioSelect.appendChild(opt);
      });
    }
  }

  departamentoSelect.addEventListener('change', function() {
    cargarMunicipios(this.value, '');
  });

  // Inicializar si hay valor
  const dep = departamentoSelect.value;
  const selectedMun = departamentoSelect.getAttribute('data-selected-mun') || '';
  cargarMunicipios(dep, selectedMun);
});
