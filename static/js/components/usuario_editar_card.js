document.addEventListener("DOMContentLoaded", function () {
  const deptoSel = document.getElementById("departamento-select");
  const municipioSelect = document.getElementById("municipio-select");

  if (!deptoSel || !municipioSelect) {
    return;
  }

  const municipiosPorDepto = {
    Risaralda: [
      "Pereira",
      "Dosquebradas",
      "Santa Rosa de Cabal",
      "Apía",
      "Balboa",
      "Belén de Umbría",
      "La Celia",
      "La Virginia",
      "Marsella",
      "Mistrató",
      "Pueblo Rico",
      "Quinchía",
      "Santuario",
    ],
    Caldas: [
      "Manizales",
      "Villamaría",
      "Aguadas",
      "Anserma",
      "Aranzazu",
      "Belalcázar",
      "Chinchiná",
      "Filadelfia",
      "La Dorada",
      "La Merced",
      "Manzanares",
      "Marmato",
      "Marquetalia",
      "Marulanda",
      "Neira",
      "Norcasia",
      "Pácora",
      "Palestina",
      "Pensilvania",
      "Riosucio",
      "Risaralda",
      "Salamina",
      "Samaná",
      "San José",
      "Supía",
      "Victoria",
      "Viterbo",
    ],
    Quindío: [
      "Armenia",
      "Buenavista",
      "Calarcá",
      "Circasia",
      "Córdoba",
      "Filandia",
      "Génova",
      "La Tebaida",
      "Montenegro",
      "Pijao",
      "Quimbaya",
      "Salento",
    ],
  };

  function actualizarMunicipios() {
    const depto = deptoSel.value;
    const municipioPrevio = municipioSelect.dataset.prevMunicipio || "";

    municipioSelect.innerHTML = '<option value="">Seleccione...</option>';

    const municipios = municipiosPorDepto[depto] || [];
    municipios.forEach(function (mun) {
      const opt = document.createElement("option");
      opt.value = mun;
      opt.textContent = mun;
      municipioSelect.appendChild(opt);
    });

    if (municipioPrevio) {
      municipioSelect.value = municipioPrevio;
    }
  }

  deptoSel.addEventListener("change", actualizarMunicipios);
  if (deptoSel.value) {
    actualizarMunicipios();
  }
});
