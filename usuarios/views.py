# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView

def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        password = request.POST.get('password')
        # Aquí luego conectamos autenticación real
        print(usuario, password)

    return render(request, 'usuarios/login.html')

def home(request):
    return redirect('login')


class Logueo(LoginView):
    template_name = "components/loggin.html"
    redirect_authenticated_user = True

