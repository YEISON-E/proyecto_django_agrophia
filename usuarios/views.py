# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

from django.views.generic.edit import CreateView,  UpdateView, DeleteView, FormView

from django.contrib.auth.views import LoginView

from django.contrib.auth.models import User

from django.urls import reverse

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
import string

import re
import os
from django.conf import settings

from .models import Shop
from .models import Register
from django.core.files.storage import FileSystemStorage
# from django.contrib.auth.decorators import login_required

def profile(request):
    return render(request, "profile.html")

def login_customer_user(request):
    if not request.user.is_authenticated:
        return redirect("usuarios:login")
    return render(request, "login_customer_user.html")

def index(request):
    if request.user.is_authenticated:
        return redirect("usuarios:login_customer_user")
    return render(request, "index.html")

class Logueo(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = False

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

        # BUSCAR EN TABLA REGISTER
        try:
            usuario_registro = Register.objects.get(numero_documento=username)
        except Register.DoesNotExist:
            register_url = reverse('usuarios:register')
            errores["general"] = f"Usuario no registrado. <a href='{register_url}' style='color:var(--terciary-500); text-decoration: underline;'>Regístrate aquí </a>"
            return render(request, self.template_name, {
                "errores": errores,
                "valores": {"username": username}
            })

        # VALIDAR CONTRASEÑA
        if usuario_registro.contrasena != password:
            errores["general"] = "Usuario o contraseña incorrectos."
            return render(request, self.template_name, {
                "errores": errores,
                "valores": {"username": username}
            })

        # OBTENER O CREAR USUARIO EN DJANGO USER
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": usuario_registro.correo_electronico,
                "first_name": usuario_registro.nombres,
                "last_name": usuario_registro.apellidos
            }
        )

        # LOGIN OK
        login(request, user)
        return redirect("usuarios:login_customer_user")


def register_step_1(request):
    if request.method == "POST":
        documento = request.POST["documento"]
        
        # Guardar datos paso 1 en sesión (método estándar Django)
        request.session["register_step_1"] = {
            "tdocumento": request.POST["tdocumento"],
            "documento": documento,
            "nombres": request.POST["nombres"],
            "apellidos": request.POST["apellidos"],
        }

        # Guardar la foto temporalmente en disco
        if request.FILES.get("foto"):
            foto_file = request.FILES["foto"]
            # Crear carpeta temporal si no existe
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_registros')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Guardar archivo con nombre basado en el documento
            ext = os.path.splitext(foto_file.name)[1]
            temp_filename = f"registro_{documento}{ext}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Guardar archivo
            with open(temp_path, 'wb') as f:
                for chunk in foto_file.chunks():
                    f.write(chunk)
            
            # Guardar ruta en sesión
            request.session["foto_temp_path"] = temp_path

        return redirect("usuarios:register2")

    return render(request, "register.html")


def register_step_2(request):
    valores = {}
    errores = {}

    if request.method == "POST":
        # Recuperar datos paso 1 desde sesión (método estándar Django)
        step1 = request.session.get("register_step_1")
        
        # Si no hay datos del paso 1, redirigir al registro
        if not step1:
            return redirect("usuarios:register")

        email = request.POST.get("email", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        password = request.POST.get("password", "").strip()
        confirm = request.POST.get("confirm_password", "").strip()
        departamento = request.POST.get("departamento", "").strip()
        municipio = request.POST.get("municipio", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        documento = step1.get("documento", "")

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
        
        # Validar contraseña
        if not password:
            errores["password"] = "La contraseña es obligatoria."
        elif len(password) < 8:
            errores["password"] = "Debe tener al menos 8 caracteres."
        elif not re.search(r'[A-Z]', password):
            errores["password"] = "Debe contener al menos una mayúscula."
        elif not re.search(r'[a-z]', password):
            errores["password"] = "Debe contener al menos una minúscula."
        elif not re.search(r'[0-9]', password):
            errores["password"] = "Debe contener al menos un número."
        elif not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            errores["password"] = "Debe contener al menos un carácter especial (!@#$%^&*)."
        elif password != confirm:
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

        # Recuperar la foto del archivo temporal
        foto_file = None
        foto_temp_path = request.session.get("foto_temp_path")
        if foto_temp_path and os.path.exists(foto_temp_path):
            from django.core.files.base import ContentFile
            # Leer el archivo temporal
            with open(foto_temp_path, 'rb') as f:
                foto_bytes = f.read()
            foto_filename = os.path.basename(foto_temp_path)
            foto_file = ContentFile(foto_bytes, name=foto_filename)

        # Guardar perfil personalizado
        register_obj = Register.objects.create(
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

        # Guardar la foto si existe
        if foto_file:
            register_obj.foto = foto_file
            register_obj.save()

        # Limpiar sesión y archivos temporales
        if "register_step_1" in request.session:
            del request.session["register_step_1"]
        if "foto_temp_path" in request.session:
            foto_temp_path = request.session.get("foto_temp_path")
            del request.session["foto_temp_path"]
            # Eliminar archivo temporal de foto
            if foto_temp_path and os.path.exists(foto_temp_path):
                try:
                    os.remove(foto_temp_path)
                except:
                    pass

        return redirect("usuarios:login")

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

        # Validar existencia y obtener usuario
        else:
            try:
                usuario = User.objects.get(email=email)
                
                # Generar código de 6 dígitos aleatorio
                codigo = ''.join(random.choices(string.digits, k=6))
                
                # Buscar registro asociado
                try:
                    registro = Register.objects.get(correo_electronico=email)
                    # Guardar código en la BD con expiración de 15 minutos
                    registro.codigo_reset = codigo
                    registro.fecha_expiracion_codigo = timezone.now() + timedelta(minutes=15)
                    registro.save()
                except Register.DoesNotExist:
                    errores["email"] = "No existe una cuenta con este correo."
                
                # Si no hay errores, enviar email
                if not errores:
                    try:
                        send_mail(
                            subject="Código para restablecer contraseña - Agrophia",
                            message=f"""
Hola {usuario.first_name},

Tu código para restablecer la contraseña es: {codigo}

Este código es válido por 15 minutos.

Si no solicitaste restablecer tu contraseña, ignora este mensaje.

Saludos,
Equipo Agrophia
                            """,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        # Guardar email en sesión y redirigir
                        request.session["reset_email"] = email
                        return redirect("usuarios:reset_password")
                    except Exception as e:
                        errores["email"] = "Error al enviar el código. Intenta nuevamente."
                        print(f"Error enviando email: {str(e)}")
            
            except User.DoesNotExist:
                # Por seguridad, mostrar mismo mensaje que si no existe
                errores["email"] = "No existe una cuenta con este correo."

    return render(request, "p_forgot-password.html", {
        "errores": errores,
        "valores": valores
    })

def restablecer_contrasena(request):
    errores = {}
    valores = {}
    email_sesion = request.session.get("reset_email")
    reset_success = request.session.pop("reset_success", False)

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
        elif not re.search(r'[A-Z]', password):
            errores["password"] = "Debe contener al menos una mayúscula."
        elif not re.search(r'[a-z]', password):
            errores["password"] = "Debe contener al menos una minúscula."
        elif not re.search(r'[0-9]', password):
            errores["password"] = "Debe contener al menos un número."
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errores["password"] = "Debe contener al menos un carácter especial (!@#$%^&*)."

        # CONFIRMAR PASSWORD
        if password != confirm_password:
            errores["confirm_password"] = "Las contraseñas no coinciden."

        # SI TODO OK, verificar código
        if not errores and email_sesion:
            try:
                registro = Register.objects.get(correo_electronico=email_sesion)
                
                # Verificar que el código sea correcto
                if registro.codigo_reset != codigo:
                    errores["codigo"] = "El código es incorrecto."
                
                # Verificar que no haya expirado
                elif timezone.now() > registro.fecha_expiracion_codigo:
                    errores["codigo"] = "El código ha expirado. Solicita uno nuevo."
                
                # Si todo está bien, cambiar la contraseña
                if not errores:
                    # Actualizar contraseña en Register
                    registro.contrasena = password
                    registro.codigo_reset = None
                    registro.fecha_expiracion_codigo = None
                    registro.save()
                    
                    # Actualizar contraseña en User de Django
                    try:
                        user = User.objects.get(email=email_sesion)
                        user.set_password(password)
                        user.save()
                    except User.DoesNotExist:
                        pass
                    
                    # Limpiar sesión y marcar exito
                    del request.session["reset_email"]
                    request.session["reset_success"] = True
                    return redirect("usuarios:reset_password")
            
            except Register.DoesNotExist:
                errores["codigo"] = "Error en el proceso de recuperación. Intenta de nuevo."
        
        elif not email_sesion:
            errores["general"] = "Primero debes ingresar tu correo. <a href='{% url \"usuarios:forgot_password\" %}'>Volver atrás</a>"

    return render(request, "reset_password.html", {
        "errores": errores,
        "valores": valores,
        "reset_success": reset_success,
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
        return redirect("usuarios:create_shop_step2")

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