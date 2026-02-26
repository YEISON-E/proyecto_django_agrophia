window.LocationUtils = {
  municipiosPorDepartamento: {
    Risaralda: [
      "Pereira",
      "Dosquebradas",
      "La Virginia",
      "Apia",
      "Balboa",
      "Belen de Umbria",
      "Guatica",
      "La Celia",
      "Marsella",
      "Mistrato",
      "Pueblo Rico",
      "Quinchia",
      "Santa Rosa de Cabal",
      "Santuario",
    ],
    Caldas: [
      "Manizales",
      "Aguadas",
      "Anserma",
      "Aranzazu",
      "Belalcazar",
      "Chinchina",
      "Filadelfia",
      "La Dorada",
      "La Merced",
      "Manzanares",
      "Marmato",
      "Marquetalia",
      "Marulanda",
      "Neira",
      "Norcasia",
      "Pacora",
      "Palestina",
      "Pensilvania",
      "Riosucio",
      "Risaralda",
      "Salamina",
      "Samana",
      "San Jose",
      "Supia",
      "Victoria",
      "Villamaria",
      "Viterbo",
    ],
    Quindio: [
      "Armenia",
      "Buenavista",
      "Calarca",
      "Circasia",
      "Cordoba",
      "Filandia",
      "Genova",
      "La Tebaida",
      "Montenegro",
      "Pijao",
      "Quimbaya",
      "Salento",
    ],
  },

  normalizarTexto(valor) {
    return (valor || "")
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .trim();
  },

  poblarMunicipios(departamento, municipioSelect) {
    if (!municipioSelect) {
      return;
    }

    municipioSelect.innerHTML = '<option value="">Selecciona el Municipio</option>';
    if (!departamento || !this.municipiosPorDepartamento[departamento]) {
      return;
    }

    this.municipiosPorDepartamento[departamento].forEach((municipio) => {
      const option = document.createElement("option");
      option.value = municipio;
      option.textContent = municipio;
      municipioSelect.appendChild(option);
    });
  },
};
