function initializeUpdatePerfilStep1() {
    const inputFoto = document.getElementById('input-foto');
    const fotoPreview = document.querySelector('.profile-update__group-file__photo_review');

    if (!inputFoto || !fotoPreview) {
        return;
    }

    inputFoto.addEventListener('change', (event) => {
        const archivo = event.target.files && event.target.files[0];
        if (!archivo) {
            return;
        }
        fotoPreview.src = URL.createObjectURL(archivo);
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpdatePerfilStep1);
} else {
    initializeUpdatePerfilStep1();
}
