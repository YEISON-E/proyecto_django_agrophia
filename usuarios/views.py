# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

from django.views.generic.edit import CreateView,  UpdateView, DeleteView, FormView

from django.contrib.auth.views import LoginView

from django.contrib import messages

from django.contrib.auth.models import User

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

import re

from .models import Shop
from .models import Register
from django.core.files.storage import FileSystemStorage
# from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, "index.html")

class Logueo(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        errores = {}

        # VALIDACIONES DOCUMENTO
        if not username:
            errores["username"] = "El número de documento es obligatorio."
        elif not username.isdigit():
            errores["username"] = "Número de documento incorrecto."
        elif len(username) < 8:
            errores["username"] = "Número de documento incorrecto."

        elif len(username) > 10:
            errores["username"] = "Número de documento incorrecto."

        # VALIDACIONES PASSWORD
        if not password:
            errores["password"] = "La contraseña es obligatoria."
        elif len(password) < 8:
            errores["password"] = "La contraseña es incorrecta."

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


def register_step_1(request):
    if request.method == "POST":
        request.session["register_step_1"] = {
            "tdocumento": request.POST["tdocumento"],
            "documento": request.POST["documento"],
            "nombres": request.POST["nombres"],
            "apellidos": request.POST["apellidos"],
        }

        if request.FILES.get("foto"):
            request.session["foto_name"] = request.FILES["foto"].name

        return redirect("register2")

    return render(request, "register.html")


def register_step_2(request):
    valores = {}
    errores = {}

    if request.method == "POST":
        step1 = request.session.get("register_step_1")

        email = request.POST.get("email", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        password = request.POST.get("password", "").strip()
        confirm = request.POST.get("confirm_password", "").strip()
        departamento = request.POST.get("departamento", "").strip()
        municipio = request.POST.get("municipio", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        documento = step1.get("documento", "") if step1 else ""

        # Guardar valores para pre-llenar en caso de error
        valores = {
            "email": email,
            "telefono": telefono,
            "departamento": departamento,
            "municipio": municipio,
            "direccion": direccion,
            "descripcion": descripcion,
        }

        # Validar que las contraseñas coincidan
        if password != confirm:
            errores["password"] = "Las contraseñas no coinciden."

        # Validar que el documento no esté registrado
        if documento and Register.objects.filter(numero_documento=documento).exists():
            errores["documento"] = "Este número de documento ya está registrado."

        # Validar que el correo no esté registrado
        if User.objects.filter(email=email).exists():
            errores["email"] = "Este correo ya está registrado."
        elif Register.objects.filter(correo_electronico=email).exists():
            errores["email"] = "Este correo ya está registrado."

        # Validar que el teléfono no esté registrado
        if Register.objects.filter(telefono=telefono).exists():
            errores["telefono"] = "Este teléfono ya está registrado."

        # Si hay errores, retornar a la plantilla con los mensajes
        if errores:
            return render(request, "register2.html", {
                "errores": errores,
                "valores": valores
            })

        # Crear usuario Django
        user = User.objects.create_user(
            username=step1["documento"],
            password=password,
            email=email
        )

        # Guardar perfil personalizado
        Register.objects.create(
            id_usuario=user.id,
            tipo_documento=step1["tdocumento"],
            numero_documento=step1["documento"],
            nombres=step1["nombres"],
            apellidos=step1["apellidos"],
            correo_electronico=email,
            telefono=telefono,
            departamento=departamento,
            municipio=municipio,
            direccion_completa=direccion,
            descripcion_perfil=descripcion,
            contrasena=password,
        )

        del request.session["register_step_1"]

        return redirect("login")

    return render(request, "register2.html", {"valores": valores, "errores": errores})

def olvidaste_contrasena(request):
    errores = {}
    valores = {}

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        valores["email"] = email

        # Validar vacío
        if not email:
            errores["email"] = "El correo es obligatorio."

        # Validar formato
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errores["email"] = "Correo electrónico inválido."

        # Validar existencia
        elif not User.objects.filter(email=email).exists():
            errores["email"] = "No existe una cuenta con este correo."

        # Si todo está bien
        if not errores:
            return render(request, "p_forgot-password.html", {
                "mensaje": "Si el correo existe, recibirás un código para restablecer tu contraseña."
            })

    return render(request, "p_forgot-password.html", {
        "errores": errores,
        "valores": valores
    })

def restablecer_contrasena(request):
    errores = {}
    valores = {}

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        valores["codigo"] = codigo

        # VALIDAR CÓDIGO
        if not codigo:
            errores["codigo"] = "El código es obligatorio."
        elif not codigo.isdigit():
            errores["codigo"] = "El código debe ser numérico."
        elif len(codigo) != 6:
            errores["codigo"] = "El código debe tener 6 dígitos."

        # VALIDAR PASSWORD
        if not password:
            errores["password"] = "La contraseña es obligatoria."
        elif len(password) < 8:
            errores["password"] = "Debe tener al menos 8 caracteres."

        # CONFIRMAR PASSWORD
        if password != confirm_password:
            errores["confirm_password"] = "Las contraseñas no coinciden."

        # SI TODO OK
        if not errores:
            #  Aquí iría:
            # - verificar código real
            # - obtener usuario
            # - user.set_password(password)
            # - user.save()

            return render(request, "reset_password.html", {
                "mensaje": "Tu contraseña ha sido restablecida correctamente."
            })

    return render(request, "reset_password.html", {
        "errores": errores,
        "valores": valores
    })

def create_shop_step1(request):
    if request.method == "POST":
        request.session["shop_step1"] = {
            "nombre": request.POST.get("nombre"),
            "telefono": request.POST.get("telefono"),
            "email": request.POST.get("email"),
            "departamento": request.POST.get("departamento"),
            "municipio": request.POST.get("municipio"),
        }
        return redirect("create_shop_step2")

    return render(request, "create-shop.html")


# PASO 2
def create_shop_step2(request):
    if request.method == "POST":
        step1 = request.session.get("shop_step1")

        Shop.objects.create(
            owner=request.user if request.user.is_authenticated else None,
            nombre=step1["nombre"],
            telefono=step1["telefono"],
            email=step1["email"],
            departamento=step1["departamento"],
            municipio=step1["municipio"],
            horario=request.POST.get("horario"),
            sitio_web=request.POST.get("sitio_web"),
            descripcion=request.POST.get("descripcion"),
        )

        # borrar sesión
        del request.session["shop_step1"]

        return redirect("index")

    return render(request, "create-shop2.html")