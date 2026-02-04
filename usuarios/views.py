# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

from django.views.generic.edit import CreateView,  UpdateView, DeleteView, FormView

from django.contrib.auth.views import LoginView

class Logueo(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True


def registrarse(request):
    if request.method == "POST":
        tdocumento = request.POST.get("tdocumento")
        documento = request.POST.get("documento")
        nombres = request.POST.get("nombres")
        apellidos = request.POST.get("apellidos")

        # Si hay archivo:
        foto = request.FILES.get("foto")

        # Aquí haces lo que quieras con esos datos:
        print(tdocumento, documento, nombres, apellidos, foto)

        # luego redireccionas
        return redirect("login")

    return render(request, "register.html")
