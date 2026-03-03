# Create your views here.
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

from django.views.generic.edit import CreateView,  UpdateView, DeleteView, FormView
from django.views.decorators.cache import never_cache

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

from .models import Register
from Tiendas.views import user_has_shop, resolve_legacy_tienda_route
from Productos.models import Product
from django.core.files.storage import FileSystemStorage
# from django.contrib.auth.decorators import login_required


def _get_register_user(request):
    register_user = Register.objects.filter(id_usuario=request.user.id).first()
    if not register_user:
        register_user = Register.objects.filter(numero_documento=request.user.username).first()
    return register_user

@never_cache
def profile(request):
    """Renderiza la vista de perfil con datos del usuario autenticado."""
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    register_user = _get_register_user(request)

    return render(request, "profile.html", {
        "register_user": register_user,
    })

@never_cache
def update_perfil(request):
    """Renderiza el paso 1 de edición de perfil."""
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    register_user = _get_register_user(request)
    if not register_user:
        return redirect("usuarios:profile")

    errores = {}
    valores = {
        "tdocumento": register_user.tipo_documento,
        "identificacion": register_user.numero_documento,
        "nombres": register_user.nombres,
        "apellidos": register_user.apellidos,
    }

    step1_session = request.session.get("update_perfil_step1")
    if step1_session:
        valores.update(step1_session)

    if request.method == "POST":
        tipo_documento = register_user.tipo_documento
        identificacion = register_user.numero_documento
        nombres = register_user.nombres
        apellidos = request.POST.get("apellidos", "").strip()

        valores = {
            "tdocumento": tipo_documento,
            "identificacion": identificacion,
            "nombres": nombres,
            "apellidos": apellidos,
        }

        if not apellidos:
            errores["apellidos"] = "El apellido es obligatorio."

        foto_file = request.FILES.get("foto")
        foto_temp_path = None
        if foto_file:
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_registros')
            os.makedirs(temp_dir, exist_ok=True)

            ext = os.path.splitext(foto_file.name)[1]
            temp_filename = f"update_{request.user.id}_{identificacion or register_user.numero_documento}{ext}"
            foto_temp_path = os.path.join(temp_dir, temp_filename)

            with open(foto_temp_path, 'wb') as temp_file:
                for chunk in foto_file.chunks():
                    temp_file.write(chunk)

        if errores:
            return render(request, "update_perfil.html", {
                "register_user": register_user,
                "errores": errores,
                "valores": valores,
            })

        request.session["update_perfil_step1"] = {
            "tdocumento": tipo_documento,
            "identificacion": identificacion,
            "nombres": nombres,
            "apellidos": apellidos,
        }

        if foto_temp_path:
            request.session["update_foto_temp_path"] = foto_temp_path

        return redirect("usuarios:update_perfil2")

    return render(request, "update_perfil.html", {
        "register_user": register_user,
        "valores": valores,
        "errores": errores,
    })

@never_cache
def update_perfil2(request):
    """Renderiza el paso 2 de edición de perfil."""
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    register_user = _get_register_user(request)
    if not register_user:
        return redirect("usuarios:profile")

    step1 = request.session.get("update_perfil_step1", {})

    errores = {}
    valores = {
        "telefono": register_user.telefono,
        "email": register_user.correo_electronico,
        "departamento": register_user.departamento,
        "municipio": register_user.municipio,
        "direccion": register_user.direccion_completa,
        "descripcion": register_user.descripcion_perfil or "",
    }

    if request.method == "POST":
        telefono = request.POST.get("telefono", "").strip()
        email = register_user.correo_electronico
        departamento = request.POST.get("departamento", "").strip()
        municipio = request.POST.get("municipio", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        current_password = request.POST.get("current_password", "").strip()
        new_password = request.POST.get("new_password", "").strip()

        valores = {
            "telefono": telefono,
            "email": email,
            "departamento": departamento,
            "municipio": municipio,
            "direccion": direccion,
            "descripcion": descripcion,
        }

        if not telefono:
            errores["telefono"] = "El teléfono es obligatorio."
        elif not telefono.isdigit() or len(telefono) < 7 or len(telefono) > 15:
            errores["telefono"] = "Número de teléfono inválido."
        elif Register.objects.exclude(pk=register_user.pk).filter(telefono=telefono).exists():
            errores["telefono"] = "Este teléfono ya está registrado."

        if not departamento:
            errores["departamento"] = "El departamento es obligatorio."
        if not municipio:
            errores["municipio"] = "El municipio es obligatorio."
        if not direccion:
            errores["direccion"] = "La dirección es obligatoria."

        if len(descripcion) > 40:
            errores["descripcion"] = "La descripción no debe superar 40 caracteres."

        if current_password or new_password:
            if not current_password:
                errores["current_password"] = "Debes ingresar tu contraseña actual."
            if not new_password:
                errores["new_password"] = "Debes ingresar una nueva contraseña."

            if current_password and not request.user.check_password(current_password):
                errores["current_password"] = "La contraseña actual es incorrecta."

            if new_password:
                if len(new_password) < 8:
                    errores["new_password"] = "Debe tener al menos 8 caracteres."
                elif not re.search(r'[A-Z]', new_password):
                    errores["new_password"] = "Debe contener al menos una mayúscula."
                elif not re.search(r'[a-z]', new_password):
                    errores["new_password"] = "Debe contener al menos una minúscula."
                elif not re.search(r'[0-9]', new_password):
                    errores["new_password"] = "Debe contener al menos un número."
                elif not re.search(r'[!@#$%^&*(),.?\":{}|<>]', new_password):
                    errores["new_password"] = "Debe contener al menos un carácter especial (!@#$%^&*)."
                elif current_password and new_password == current_password:
                    errores["new_password"] = "La nueva contraseña debe ser diferente a la actual."

        if errores:
            return render(request, "update-perfil2.html", {
                "register_user": register_user,
                "errores": errores,
                "valores": valores,
            })

        tipo_documento = step1.get("tdocumento", register_user.tipo_documento)
        identificacion = step1.get("identificacion", register_user.numero_documento)
        nombres = step1.get("nombres", register_user.nombres)
        apellidos = step1.get("apellidos", register_user.apellidos)

        register_user.tipo_documento = tipo_documento
        register_user.numero_documento = identificacion
        register_user.nombres = nombres
        register_user.apellidos = apellidos
        register_user.telefono = telefono
        register_user.correo_electronico = email
        register_user.departamento = departamento
        register_user.municipio = municipio
        register_user.direccion_completa = direccion
        register_user.descripcion_perfil = descripcion

        if new_password:
            register_user.contrasena = new_password

        foto_temp_path = request.session.get("update_foto_temp_path")
        if foto_temp_path and os.path.exists(foto_temp_path):
            from django.core.files.base import ContentFile
            with open(foto_temp_path, 'rb') as photo_file:
                photo_bytes = photo_file.read()
            foto_filename = os.path.basename(foto_temp_path)
            register_user.foto.save(foto_filename, ContentFile(photo_bytes), save=False)
            os.remove(foto_temp_path)

        register_user.save()

        request.user.username = identificacion
        request.user.email = email
        request.user.first_name = nombres
        request.user.last_name = apellidos
        if new_password:
            request.user.set_password(new_password)
        request.user.save()
        if new_password:
            update_session_auth_hash(request, request.user)

        request.session.pop("update_perfil_step1", None)
        request.session.pop("update_foto_temp_path", None)

        return redirect("usuarios:profile")

    return render(request, "update-perfil2.html", {
        "register_user": register_user,
        "valores": valores,
        "errores": errores,
    })

@never_cache
def login_customer_user(request):
    """
    Home de usuario autenticado.
    Si el usuario ya tiene una tienda creada, redirige al panel de agricultor.
    """
    if not request.user.is_authenticated:
        return redirect("usuarios:login")
    if user_has_shop(request.user):
        return redirect("tiendas:interface_farmer")

    productos = Product.objects.prefetch_related("images").order_by("-created_at")

    return render(request, "login_customer_user.html", {
        "productos": productos,
    })

def index(request):
    """Página pública principal. Si está autenticado, redirige al home interno."""
    if request.user.is_authenticated:
        return redirect("usuarios:login_customer_user")
    return render(request, "index.html")

def legacy_frontend_view(request, page):
    """
    Compatibilidad con rutas legacy del frontend estático.
    Mapea URLs antiguas a vistas/plantillas Django actuales.
    """
    tienda_action = resolve_legacy_tienda_route(page)
    if tienda_action:
        mode, target = tienda_action
        if mode == "template":
            return render(request, target)
        return redirect(target)

    legacy_routes = {
        "p_login-customer.html": ("redirect", "usuarios:login_customer_user"),
        "p_login-customer-vegetables.html": ("redirect", "usuarios:login_customer_user"),
        "p_login-customer-dairy.html": ("redirect", "usuarios:login_customer_user"),
        "shopping.html": ("redirect", "carrito_compras:shopping_cart"),
        "mensajes_sends.html": ("redirect", "usuarios:login_customer_user"),
        "my_orders.html": ("redirect", "usuarios:login_customer_user"),
        "contact.html": ("template", "contact.html"),
        "profile.html": ("redirect", "usuarios:profile"),
        "update_perfil.html": ("redirect", "usuarios:update_perfil"),
        "update-perfil2.html": ("redirect", "usuarios:update_perfil2"),
        "index.html": ("redirect", "usuarios:index"),
    }

    action = legacy_routes.get(page)
    if not action:
        return redirect("usuarios:index")

    mode, target = action
    if mode == "template":
        return render(request, target)

    return redirect(target)

def logout_user(request):
    """
    Cierra sesión y aplica cabeceras no-cache para evitar volver a vistas protegidas con botón atrás.
    """
    logout(request)
    response = redirect("usuarios:index")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

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

