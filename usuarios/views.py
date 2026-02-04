# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

from django.views.generic.edit import CreateView,  UpdateView, DeleteView, FormView

from django.contrib.auth.views import LoginView

from django.contrib import messages

class Logueo(LoginView):
    template_name = "login.html"

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

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        errores = {}

        # VALIDACIONES DOCUMENTO
        if not username:
            errores["username"] = "El número de documento es obligatorio."
        elif not username.isdigit():
            errores["username"] = "El documento solo debe contener números."
        elif len(username) < 8:
            errores["username"] = "El documento es demasiado corto."

        elif len(username) > 10:
            errores["username"] = "El documento es demasiado largo."

        # VALIDACIONES PASSWORD
        if not password:
            errores["password"] = "La contraseña es obligatoria."
        elif len(password) < 8:
            errores["password"] = "La contraseña es demasiado corta."

        # Si hay errores, renderiza de nuevo con errores
        if errores:
            return render(request, self.template_name, {
                "errores": errores,
                "valores": {"username": username}
            })

        # AUTENTICAR
        user = authenticate(request, username=username, password=password)

        if user is None:
            errores["general"] = "Documento o contraseña incorrectos."
            return render(request, self.template_name, {
                "errores": errores,
                "valores": {"username": username}
            })

        # LOGIN OK
        login(request, user)
        return redirect("login")  # o a donde quieras

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
