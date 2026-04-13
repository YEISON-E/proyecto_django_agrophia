"""Vistas base del proyecto Agrophia.

Este modulo contiene vistas generales de arranque del sitio.
Actualmente expone la vista `home`, que renderiza la portada principal.
"""

from django.shortcuts import render, redirect

def home(request):
    """Renderiza la pagina principal del proyecto."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    return render(request, 'index.html')
