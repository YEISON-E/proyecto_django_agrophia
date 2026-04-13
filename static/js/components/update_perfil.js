function initializeUpdatePerfilStep1() {
    const inputFoto = document.getElementById('input-foto');
    let fotoPreview = document.getElementById('preview-update') || document.querySelector('.profile-update__group-file__photo_review');
    let previousObjectUrl = null;

    if (!inputFoto || !fotoPreview) {
        return;
    }

    inputFoto.addEventListener('change', (event) => {
        const archivo = event.target.files && event.target.files[0];
        if (!archivo) {
            return;
        }

        if (fotoPreview.tagName !== 'IMG') {
            const replacement = document.createElement('img');
            replacement.id = 'preview-update';
            replacement.alt = 'foto de Perfil cargada';
            replacement.className = 'profile-update__group-file__photo_review';
            fotoPreview.replaceWith(replacement);
            fotoPreview = replacement;
        }

        if (previousObjectUrl) {
            URL.revokeObjectURL(previousObjectUrl);
        }
        previousObjectUrl = URL.createObjectURL(archivo);
        fotoPreview.src = previousObjectUrl;
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpdatePerfilStep1);
} else {
    initializeUpdatePerfilStep1();
}
