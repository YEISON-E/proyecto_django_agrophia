"""Vistas base del proyecto Agrophia.

Este modulo contiene vistas generales de arranque del sitio.
Actualmente expone la vista `home`, que renderiza la portada principal.
"""

from django.shortcuts import render, redirect

def home(request):
    """Renderiza la pagina principal del proyecto."""
    return render(request, 'index.html')
