# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        clave = request.POST.get('clave')

        user = authenticate(request, username=usuario, password=clave)

        if user is not None:
            login(request, user)
            return redirect('login')  # cámbialo luego a dashboard

        return render(request, 'usuarios/login.html', {
            'error': 'Usuario o contraseña incorrectos'
        })

    return render(request, 'usuarios/login.html')
