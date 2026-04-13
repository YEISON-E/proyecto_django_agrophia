function initializeUpdatePerfilStep2() {
    const departamentoSelect = document.getElementById('input-departament');
    const municipioSelect = document.getElementById('input-municipality');
    const telefonoInput = document.getElementById('input-telefono');
    const showPasswordCheckbox = document.getElementById('show-password');
    const currentPasswordInput = document.getElementById('input-password');
    const newPasswordInput = document.getElementById('input-new-password');

    if (!departamentoSelect || !municipioSelect) {
        return;
    }

    const normalizarTexto = (valor) => {
        if (window.LocationUtils && typeof window.LocationUtils.normalizarTexto === 'function') {
            return window.LocationUtils.normalizarTexto(valor || '');
        }
        return (valor || '').normalize('NFD').replace(/\p{Diacritic}/gu, '').trim();
    };

    const preseleccionado = municipioSelect.dataset.selected || municipioSelect.value || '';

    const poblarMunicipios = () => {
        const departamento = departamentoSelect.value || '';

        if (window.LocationUtils && typeof window.LocationUtils.poblarMunicipios === 'function') {
            window.LocationUtils.poblarMunicipios(departamento, municipioSelect);
        } else {
            municipioSelect.innerHTML = '<option value="">Selecciona el Municipio</option>';
        }
    };

    const seleccionarMunicipioSiExiste = (valorMunicipio) => {
        if (!valorMunicipio) {
            return;
        }

        const valorNormalizado = normalizarTexto(valorMunicipio).toLowerCase();
        const opcion = Array.from(municipioSelect.options).find((option) => {
            return normalizarTexto(option.value).toLowerCase() === valorNormalizado;
        });

        if (opcion) {
            municipioSelect.value = opcion.value;
        }
    };

    poblarMunicipios();
    seleccionarMunicipioSiExiste(preseleccionado);

    departamentoSelect.addEventListener('change', () => {
        poblarMunicipios();
    });

    if (showPasswordCheckbox) {
        showPasswordCheckbox.addEventListener('change', () => {
            const inputType = showPasswordCheckbox.checked ? 'text' : 'password';

            if (currentPasswordInput) {
                currentPasswordInput.type = inputType;
            }
            if (newPasswordInput) {
                newPasswordInput.type = inputType;
            }
        });
    }

    if (telefonoInput) {
        const validatePhone = () => {
            const digitsOnly = (telefonoInput.value || '').replace(/\D/g, '').slice(0, 10);
            if (telefonoInput.value !== digitsOnly) {
                telefonoInput.value = digitsOnly;
            }

            const phoneValue = telefonoInput.value;
            if (!phoneValue) {
                telefonoInput.setCustomValidity('Teléfono obligatorio.');
            } else if (!phoneValue.startsWith('3')) {
                telefonoInput.setCustomValidity('Debe iniciar en 3.');
            } else if (phoneValue.length !== 10) {
                telefonoInput.setCustomValidity('Usa 10 dígitos.');
            } else if (!/^3\d{9}$/.test(phoneValue)) {
                telefonoInput.setCustomValidity('Solo números.');
            } else {
                telefonoInput.setCustomValidity('');
            }
        };

        telefonoInput.addEventListener('input', validatePhone);
        telefonoInput.addEventListener('blur', validatePhone);
        validatePhone();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpdatePerfilStep2);
} else {
    initializeUpdatePerfilStep2();
}
