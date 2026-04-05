"""
Vistas del modulo de usuarios.

Este archivo centraliza autenticacion, registro y gestion de perfil:
- Inicio/cierre de sesion para clientes y administradores.
- Control de seguridad de login (intentos fallidos, bloqueo temporal y 2FA admin).
- Registro de usuarios en dos pasos con archivos temporales.
- Actualizacion de perfil en dos pasos y cambio de contrasena.
- Recuperacion de contrasena mediante codigo por correo.
- Rutas publicas, compatibilidad legacy y vistas legales.

Nota:
Por su alcance, este archivo contiene utilidades auxiliares para validaciones,
sincronizacion entre `Register` y `User`, y navegacion segura con parametro next.
"""
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

from django.views.generic.edit import CreateView,  UpdateView, DeleteView, FormView
from django.views.decorators.cache import never_cache

from django.contrib.auth.views import LoginView

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password, identify_hasher, make_password

from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlparse

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.core.mail import send_mail
from django.core import signing
from django.utils import timezone
from datetime import timedelta
# Importación de dependencias necesarias para ejecutar esta vista.
import math
import random
import string
import time

import re
import os
from django.conf import settings

from .models import Register
from Tiendas.views import user_has_shop, resolve_legacy_tienda_route
from Productos.models import Product
from django.core.files.storage import FileSystemStorage
# from django.contrib.auth.decorators import login_required


PASSWORD_ALLOWED_RE = re.compile(r'^[A-Za-z0-9!@#$%^&*(),.?":{}|<>]+$')
MAX_FAILED_LOGIN_ATTEMPTS = 3
LOCKOUT_MINUTES = 30


def _validate_password_policy(password):
    """Valida la politica de contrasena y retorna mensaje de error o `None`."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not password:
        return "La contraseña es obligatoria."
    if len(password) < 8:
        return "Debe tener al menos 8 caracteres."
    # Control de flujo y validación de condiciones del proceso.
    if len(password) > 20:
        return "La contraseña no debe superar 20 caracteres."
    if re.search(r"\s", password):
        return "La contraseña no puede contener espacios."
    # Control de flujo y validación de condiciones del proceso.
    if not PASSWORD_ALLOWED_RE.fullmatch(password):
        return "La contraseña contiene caracteres no permitidos."
    if not re.search(r'[A-Z]', password):
        return "Debe contener al menos una mayúscula."
    # Control de flujo y validación de condiciones del proceso.
    if not re.search(r'[a-z]', password):
        return "Debe contener al menos una minúscula."
    if not re.search(r'[0-9]', password):
        return "Debe contener al menos un número."
    # Control de flujo y validación de condiciones del proceso.
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Debe contener al menos un carácter especial (!@#$%^&*)."
    return None


def _is_hashed_password(value):
    """Indica si una cadena corresponde a un hash reconocido por Django."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not value:
        return False
    try:
        identify_hasher(value)
        # Retorno de respuesta según el estado y resultado de la operación.
        return True
    except Exception:
        return False


def _verify_register_password(register_user, raw_password):
    """Verifica contrasena contra `Register`, soportando hash o texto legacy."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    stored_password = (register_user.contrasena or "").strip()
    if not stored_password:
        return False
    if _is_hashed_password(stored_password):
        # Retorno de respuesta según el estado y resultado de la operación.
        return check_password(raw_password, stored_password)
    return stored_password == raw_password


def _set_register_password(register_user, raw_password, save=True):
    """Guarda la contrasena en `Register` usando hash seguro de Django."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    register_user.contrasena = make_password(raw_password)
    if save:
        register_user.save(update_fields=["contrasena"])


def _send_temporary_lock_email(register_user, blocked_until):
    """Envia correo notificando bloqueo temporal por intentos fallidos."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    local_blocked_until = timezone.localtime(blocked_until)
    tz_name = timezone.get_current_timezone_name()

    send_mail(
        subject='Bloqueo temporal por intentos fallidos - Agrophia',
        message=(
            'Detectamos multiples intentos fallidos de inicio de sesion en tu cuenta.\n\n'
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            'Tu cuenta ha sido bloqueada temporalmente hasta: '
            f'{local_blocked_until.strftime("%Y-%m-%d %H:%M:%S")} ({tz_name}).\n'
            'Podras intentar iniciar sesion nuevamente despues de 30 minutos.\n\n'
            'Si no reconoces esta actividad, te recomendamos cambiar tu contraseña cuando recuperes el acceso.'
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[register_user.correo_electronico],
        fail_silently=False,
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    )


def _get_register_user(request):
    """Obtiene el perfil `Register` del usuario autenticado actual."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    register_user = Register.objects.filter(id_usuario=request.user.id).first()
    if not register_user:
        register_user = Register.objects.filter(numero_documento=request.user.username).first()
    return register_user


def _resolve_safe_next_url(request, default_name="usuarios:profile"):
    """Resuelve un destino `next` seguro y permitido para redireccion."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    candidate = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.session.get("update_perfil_next")
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    )

    if candidate and url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    ):
        request.session["update_perfil_next"] = candidate
        return candidate

    fallback = reverse(default_name)
    request.session["update_perfil_next"] = fallback
    return fallback

@never_cache
def profile(request):
    """Renderiza la vista de perfil con datos del usuario autenticado."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    register_user = _get_register_user(request)

    return render(request, "profile.html", {
        "register_user": register_user,
    })

@never_cache
def update_perfil(request):
    """Renderiza el paso 1 de edición de perfil."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    register_user = _get_register_user(request)
    if not register_user:
        return redirect("usuarios:profile")

    next_url = _resolve_safe_next_url(request)

    errores = {}
    valores = {
        "tdocumento": register_user.tipo_documento,
        "identificacion": register_user.numero_documento,
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
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
        # Actualización de estado intermedio que será utilizada en pasos posteriores.
        apellidos = request.POST.get("apellidos", "").strip()

        valores = {
            "tdocumento": tipo_documento,
            "identificacion": identificacion,
            "nombres": nombres,
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            "apellidos": apellidos,
        }

        if not apellidos:
            errores["apellidos"] = "El apellido es obligatorio."

        foto_file = request.FILES.get("foto")
        foto_temp_path = None
        if foto_file:
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_registros')
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
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
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                "valores": valores,
                "next_url": next_url,
            })

        request.session["update_perfil_step1"] = {
            "tdocumento": tipo_documento,
            "identificacion": identificacion,
            "nombres": nombres,
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            "apellidos": apellidos,
        }

        if foto_temp_path:
            request.session["update_foto_temp_path"] = foto_temp_path

        return redirect("usuarios:update_perfil2")

    return render(request, "update_perfil.html", {
        "register_user": register_user,
        "valores": valores,
        "errores": errores,
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "next_url": next_url,
    })

@never_cache
def update_perfil2(request):
    """Renderiza el paso 2 de edición de perfil."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    register_user = _get_register_user(request)
    if not register_user:
        return redirect("usuarios:profile")

    next_url = _resolve_safe_next_url(request)

    step1 = request.session.get("update_perfil_step1", {})

    errores = {}
    valores = {
        "telefono": register_user.telefono,
        "email": register_user.correo_electronico,
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "departamento": register_user.departamento,
        "municipio": register_user.municipio,
        "direccion": register_user.direccion_completa,
        "descripcion": register_user.descripcion_perfil or "",
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    }

    if request.method == "POST":
        telefono = request.POST.get("telefono", "").strip()
        email = register_user.correo_electronico
        departamento = request.POST.get("departamento", "").strip()
        # Actualización de estado intermedio que será utilizada en pasos posteriores.
        municipio = request.POST.get("municipio", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        current_password = request.POST.get("current_password", "").strip()
        # Actualización de estado intermedio que será utilizada en pasos posteriores.
        new_password = request.POST.get("new_password", "").strip()

        valores = {
            "telefono": telefono,
            "email": email,
            "departamento": departamento,
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            "municipio": municipio,
            "direccion": direccion,
            "descripcion": descripcion,
        }

        if not telefono:
            errores["telefono"] = "El teléfono es obligatorio."
        elif not telefono.isdigit() or len(telefono) < 7 or len(telefono) > 15:
            errores["telefono"] = "Número de teléfono inválido."
        # Control de flujo y validación de condiciones del proceso.
        elif Register.objects.exclude(pk=register_user.pk).filter(telefono=telefono).exists():
            errores["telefono"] = "Este teléfono ya está registrado."

        if not departamento:
            errores["departamento"] = "El departamento es obligatorio."
        if not municipio:
            errores["municipio"] = "El municipio es obligatorio."
        # Control de flujo y validación de condiciones del proceso.
        if not direccion:
            errores["direccion"] = "La dirección es obligatoria."

        if len(descripcion) > 120:
            errores["descripcion"] = "La descripción no debe superar 120 caracteres."

        if current_password or new_password:
            if not current_password:
                errores["current_password"] = "Debes ingresar tu contraseña actual."
            if not new_password:
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                errores["new_password"] = "Debes ingresar una nueva contraseña."

            if current_password and not request.user.check_password(current_password):
                errores["current_password"] = "La contraseña actual es incorrecta."

            if new_password:
                password_error = _validate_password_policy(new_password)
                if password_error:
                    errores["new_password"] = password_error
                # Control de flujo y validación de condiciones del proceso.
                elif current_password and new_password == current_password:
                    errores["new_password"] = "La nueva contraseña debe ser diferente a la actual."

        if errores:
            return render(request, "update-perfil2.html", {
                "register_user": register_user,
                "errores": errores,
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                "valores": valores,
                "next_url": next_url,
            })

        tipo_documento = step1.get("tdocumento", register_user.tipo_documento)
        identificacion = step1.get("identificacion", register_user.numero_documento)
        nombres = step1.get("nombres", register_user.nombres)
        apellidos = step1.get("apellidos", register_user.apellidos)

        register_user.tipo_documento = tipo_documento
        register_user.numero_documento = identificacion
        register_user.nombres = nombres
        register_user.apellidos = apellidos
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        register_user.telefono = telefono
        register_user.correo_electronico = email
        register_user.departamento = departamento
        register_user.municipio = municipio
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        register_user.direccion_completa = direccion
        register_user.descripcion_perfil = descripcion

        if new_password:
            _set_register_password(register_user, new_password, save=False)

        foto_temp_path = request.session.get("update_foto_temp_path")
        if foto_temp_path and os.path.exists(foto_temp_path):
            from django.core.files.base import ContentFile
            with open(foto_temp_path, 'rb') as photo_file:
                # Actualización de estado intermedio que será utilizada en pasos posteriores.
                photo_bytes = photo_file.read()
            foto_filename = os.path.basename(foto_temp_path)
            register_user.foto.save(foto_filename, ContentFile(photo_bytes), save=False)
            os.remove(foto_temp_path)

        register_user.save()

        request.user.username = identificacion
        request.user.email = email
        request.user.first_name = nombres
        request.user.last_name = apellidos
        # Control de flujo y validación de condiciones del proceso.
        if new_password:
            request.user.set_password(new_password)
        request.user.save()
        if new_password:
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            update_session_auth_hash(request, request.user)

        request.session.pop("update_perfil_step1", None)
        request.session.pop("update_foto_temp_path", None)

        return redirect(next_url)

    return render(request, "update-perfil2.html", {
        "register_user": register_user,
        "valores": valores,
        "errores": errores,
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "next_url": next_url,
    })

@never_cache
def login_customer_user(request):
    """
    Home de usuario autenticado.
    Si el usuario ya tiene una tienda creada, redirige al panel de agricultor.
    """
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    # Mostrar mensaje importante del admin si existe
    from Mensajes.models import AdminToUserMessage
    from usuarios.models import Register
    # Buscar por id_usuario o por número_documento (username)
    register_user = Register.objects.filter(id_usuario=request.user.id).first()
    if not register_user:
        register_user = Register.objects.filter(numero_documento=request.user.username).first()
    mensaje_admin = None
    # Control de flujo y validación de condiciones del proceso.
    if register_user:
        mensaje_admin = AdminToUserMessage.objects.filter(usuario=register_user, leido=False).order_by('-creado').first()
        # Ya no se marca como leído aquí, se hará por AJAX al cerrar el modal
    force_customer_home = request.session.pop("force_customer_home", False)
    if user_has_shop(request.user) and not force_customer_home:
        return redirect("tiendas:interface_farmer")

    productos = Product.objects.filter(
        is_active=True,
        stock__gt=0,
        shop__is_active=True,
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    ).prefetch_related("images").order_by("-created_at")

    customer_home_notice = request.session.pop("customer_home_notice", "")

    print("[DEBUG] Usuario autenticado:", request.user)
    print("[DEBUG] Register encontrado:", register_user)
    print("[DEBUG] mensaje_admin:", mensaje_admin)
    return render(request, "login_customer_user.html", {
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "productos": productos,
        "customer_home_notice": customer_home_notice,
        "mensaje_admin": mensaje_admin,
    })


@never_cache
def mensajes_sends(request):
    """
    Gestiona la vista Mensajes sends.
    
    Aplica validaciones de entrada, reglas de negocio y
    devuelve una respuesta HTTP coherente con el estado del proceso.
    """
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not request.user.is_authenticated:
        return redirect("usuarios:login")

    return redirect("mensajes:sent_messages")

def index(request):
    """Página pública principal. Siempre muestra el index público y cierra sesión si hay usuario autenticado."""

    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if request.user.is_authenticated:
        # Si es admin, redirigir al home de admin
        try:
            reg = Register.objects.get(id_usuario=request.user.id)
            if reg.estado == 'admin':
                return redirect('/administrador/home/')
        # Control de flujo y validación de condiciones del proceso.
        except Register.DoesNotExist:
            pass
        # Si no es admin, cerrar sesión y limpiar sesión
        logout(request)
        request.session.flush()

    productos = Product.objects.filter(
        is_active=True,
        stock__gt=0,
        shop__is_active=True,
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    ).prefetch_related("images").order_by("-created_at")

    return render(request, "index.html", {
        "productos": productos,
    })


def public_products(request):
    """Pagina publica de productos sin hero ni seccion informativa."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if request.user.is_authenticated:
        return redirect("usuarios:home_customer")

    productos = Product.objects.filter(
        is_active=True,
        stock__gt=0,
        shop__is_active=True,
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    ).prefetch_related("images").order_by("-created_at")

    return render(request, "products_public.html", {
        "productos": productos,
    })

def legacy_frontend_view(request, page):
    """
    Compatibilidad con rutas legacy del frontend estático.
    Mapea URLs antiguas a vistas/plantillas Django actuales.
    """
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    tienda_action = resolve_legacy_tienda_route(page)
    if tienda_action:
        mode, target = tienda_action
        if mode == "template":
            # Retorno de respuesta según el estado y resultado de la operación.
            return render(request, target)
        return redirect(target)

    legacy_routes = {
        "p_login-customer.html": ("redirect", "usuarios:home_customer"),
        "p_login-customer-vegetables.html": ("redirect", "usuarios:home_customer"),
        "p_login-customer-dairy.html": ("redirect", "usuarios:home_customer"),
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "p_card-available.html": ("redirect", "usuarios:public_products"),
        "shopping.html": ("redirect", "carrito_compras:shopping_cart"),
        "mensajes_sends.html": ("redirect", "mensajes:sent_messages"),
        "my_orders.html": ("redirect", "pedidos:orders_client"),
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "contact.html": ("template", "contact.html"),
        "profile.html": ("redirect", "usuarios:profile"),
        "update_perfil.html": ("redirect", "usuarios:update_perfil"),
        "update-perfil2.html": ("redirect", "usuarios:update_perfil2"),
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "index.html": ("redirect", "usuarios:index"),
    }

    action = legacy_routes.get(page)
    if not action:
        if page.startswith("components/"):
            return HttpResponse("", status=404)
        # Retorno de respuesta según el estado y resultado de la operación.
        return redirect("usuarios:index")

    mode, target = action
    if mode == "template":
        return render(request, target)

    return redirect(target)

def logout_user(request):
    """
    Cierra sesión y aplica cabeceras no-cache para evitar volver a vistas protegidas con botón atrás.
    """
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    logout(request)
    response = redirect("usuarios:index")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    # Paso de apoyo dentro del flujo principal de la funcionalidad.
    response["Expires"] = "0"
    return response

class Logueo(LoginView):
    """
    Define la clase Logueo y su comportamiento dentro del flujo de vistas.
    """
    template_name = "login.html"
    redirect_authenticated_user = False

    def post(self, request, *args, **kwargs):
        # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
        # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
        """Procesa login con reglas de seguridad y flujo especial para admin.

        Incluye validaciones de formato, control de intentos fallidos,
        bloqueo temporal, sincronizacion `Register`/`User` y 2FA por codigo
        para cuentas administrativas.
        """
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        errores = {}

        # 1) Validaciones de formato rapido de credenciales.
        # VALIDACIONES DOCUMENTO
        if not username:
            errores["username"] = "El número de documento es obligatorio."
        elif not username.isdigit():
            errores["username"] = "Número de documento incorrecto."
        # Control de flujo y validación de condiciones del proceso.
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
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            })

        # 2) Carga perfil de negocio (Register) asociado al documento.
        # BUSCAR EN TABLA REGISTER
        try:
            usuario_registro = Register.objects.get(numero_documento=username)
        except Register.DoesNotExist:
            register_url = reverse('usuarios:register')
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            errores["general"] = f"Usuario no registrado. <a href='{register_url}' style='color:var(--terciary-500); text-decoration: underline;'>Regístrate aquí </a>"
            return render(request, self.template_name, {
                "errores": errores,
                "valores": {"username": username}
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            })

        now = timezone.now()

    # 3) Gestiona ventana de bloqueo temporal por intentos fallidos.
        # Si ya paso el tiempo de bloqueo, limpiar estado para reiniciar conteo.
        if usuario_registro.blocked_until and usuario_registro.blocked_until <= now:
            usuario_registro.blocked_until = None
            usuario_registro.failed_login_attempts = 0
            usuario_registro.save(update_fields=["blocked_until", "failed_login_attempts"])

        if usuario_registro.blocked_until and usuario_registro.blocked_until > now:
            remaining_seconds = (usuario_registro.blocked_until - now).total_seconds()
            remaining_minutes = max(1, math.ceil(remaining_seconds / 60))
            errores["general"] = (
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                "Tu cuenta esta bloqueada temporalmente por multiples intentos fallidos. "
                f"Intenta nuevamente en {remaining_minutes} minuto(s)."
            )
            return render(request, self.template_name, {
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                "errores": errores,
                "valores": {"username": username}
            })

        # 4) Verifica contrasena y actualiza contador/estado de bloqueo.
        # VALIDAR CONTRASEÑA
        if not _verify_register_password(usuario_registro, password):
            failed_attempts = (usuario_registro.failed_login_attempts or 0) + 1

            if failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                blocked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                usuario_registro.failed_login_attempts = failed_attempts
                usuario_registro.blocked_until = blocked_until
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                usuario_registro.save(update_fields=["failed_login_attempts", "blocked_until"])

                try:
                    _send_temporary_lock_email(usuario_registro, blocked_until)
                except Exception:
                    # No interrumpir el flujo de login si el correo falla.
                    pass

                errores["general"] = (
                    "Has superado los 3 intentos de contraseña incorrecta. "
                    "Tu cuenta fue bloqueada por 30 minutos y enviamos una notificacion a tu correo."
                )
            # Control de flujo y validación de condiciones del proceso.
            else:
                usuario_registro.failed_login_attempts = failed_attempts
                usuario_registro.save(update_fields=["failed_login_attempts"])
                remaining_attempts = MAX_FAILED_LOGIN_ATTEMPTS - failed_attempts
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                errores["general"] = (
                    "Usuario o contraseña incorrectos. "
                    f"Te quedan {remaining_attempts} intento(s)."
                )

            return render(request, self.template_name, {
                "errores": errores,
                "valores": {"username": username}
            })

        if usuario_registro.failed_login_attempts or usuario_registro.blocked_until:
            usuario_registro.failed_login_attempts = 0
            usuario_registro.blocked_until = None
            usuario_registro.save(update_fields=["failed_login_attempts", "blocked_until"])

        # Migra en caliente cualquier contraseña legacy en texto plano.
        if not _is_hashed_password(usuario_registro.contrasena):
            _set_register_password(usuario_registro, password)

        # 5) Si la cuenta esta inactiva/bloqueada, registra notificacion al admin.
        # VALIDAR ESTADO
        if usuario_registro.estado not in ['activo', 'admin']:
            try:
                from Mensajes.models import AdminNotification

                sender_user = None
                if usuario_registro.id_usuario:
                    sender_user = User.objects.filter(id=usuario_registro.id_usuario).first()
                if sender_user is None:
                    # Actualización de estado intermedio que será utilizada en pasos posteriores.
                    sender_user = User.objects.filter(username=username).first()
                if sender_user is None:
                    sender_user = User.objects.create_user(
                        username=username,
                        # Actualización de estado intermedio que será utilizada en pasos posteriores.
                        password=None,
                        email=usuario_registro.correo_electronico,
                        first_name=usuario_registro.nombres,
                        last_name=usuario_registro.apellidos,
                    # Paso de apoyo dentro del flujo principal de la funcionalidad.
                    )

                if usuario_registro.id_usuario != sender_user.id:
                    usuario_registro.id_usuario = sender_user.id
                    usuario_registro.save(update_fields=["id_usuario"])

                last_window = timezone.now() - timedelta(minutes=10)
                already_notified = AdminNotification.objects.filter(
                    notification_type=AdminNotification.TYPE_BLOCKED_LOGIN_ATTEMPT,
                    sender_register=usuario_registro,
                    # Actualización de estado intermedio que será utilizada en pasos posteriores.
                    created_at__gte=last_window,
                ).exists()

                if not already_notified:
                    AdminNotification.objects.create(
                        notification_type=AdminNotification.TYPE_BLOCKED_LOGIN_ATTEMPT,
                        sender_user=sender_user,
                        # Actualización de estado intermedio que será utilizada en pasos posteriores.
                        sender_register=usuario_registro,
                        product=None,
                        message=(
                            "El usuario bloqueado intento iniciar sesion. "
                            # Paso de apoyo dentro del flujo principal de la funcionalidad.
                            f"Documento: {usuario_registro.numero_documento}."
                        ),
                    )
            except Exception:
                # Nunca bloquear el flujo de login por errores de notificación.
                pass

            errores["general"] = "Tu cuenta está bloqueada o inactiva. Contacta al administrador."
            blocked_account_token = signing.dumps({
                "register_id": usuario_registro.id,
                "documento": usuario_registro.numero_documento,
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            })
            return render(request, self.template_name, {
                "errores": errores,
                "valores": {"username": username},
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                "blocked_account_message": "Este usuario fue deshabilitado por el administrador. Si deseas recuperar el acceso, por favor comunicate con soporte o con el administrador.",
                "blocked_account_token": blocked_account_token,
            })

        # 6) Sincroniza/crea usuario auth de Django vinculado al perfil Register.
        # Resolver primero el usuario auth asociado al Register para no perder
        # la relación Shop.owner cuando el id ya existe en base de datos.
        user = None
        if usuario_registro.id_usuario:
            user = User.objects.filter(id=usuario_registro.id_usuario).first()

        if user is None:
            user = User.objects.filter(username=username).first()

        if user is None:
            user = User.objects.create_user(
                username=username,
                password=password,
                # Actualización de estado intermedio que será utilizada en pasos posteriores.
                email=usuario_registro.correo_electronico,
                first_name=usuario_registro.nombres,
                last_name=usuario_registro.apellidos,
            )
        # Control de flujo y validación de condiciones del proceso.
        else:
            fields_to_update = []
            if user.username != username:
                username_in_use = User.objects.exclude(id=user.id).filter(username=username).exists()
                # Control de flujo y validación de condiciones del proceso.
                if not username_in_use:
                    user.username = username
                    fields_to_update.append("username")
            if user.email != usuario_registro.correo_electronico:
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                user.email = usuario_registro.correo_electronico
                fields_to_update.append("email")
            if user.first_name != usuario_registro.nombres:
                user.first_name = usuario_registro.nombres
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                fields_to_update.append("first_name")
            if user.last_name != usuario_registro.apellidos:
                user.last_name = usuario_registro.apellidos
                fields_to_update.append("last_name")
            # Control de flujo y validación de condiciones del proceso.
            if not user.check_password(password):
                user.set_password(password)
                fields_to_update.append("password")
            if fields_to_update:
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                user.save(update_fields=fields_to_update)

        if usuario_registro.id_usuario != user.id:
            usuario_registro.id_usuario = user.id
            usuario_registro.save(update_fields=["id_usuario"])

        # 7) Login base exitoso; para admin exige segundo factor por correo.
        # LOGIN OK
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # Si es admin, exigir segundo factor antes de entrar al panel.
        if usuario_registro.estado == 'admin':
            raw_next = (
                request.POST.get('next')
                or request.GET.get('next')
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                or request.session.get('pending_admin_next')
                or reverse('administrador:home_admin')
            )
            parsed_next = urlparse(raw_next)
            # Actualización de estado intermedio que será utilizada en pasos posteriores.
            admin_next_path = parsed_next.path or reverse('administrador:home_admin')
            if not admin_next_path.startswith('/administrador/'):
                admin_next_path = reverse('administrador:home_admin')

            admin_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            expires_at = timezone.now() + timedelta(minutes=2)

            usuario_registro.admin_code_validated = False
            usuario_registro.save(update_fields=['admin_code_validated'])

            request.session['pending_admin_user_id'] = user.id
            request.session['pending_admin_register_id'] = usuario_registro.id
            request.session['pending_admin_code'] = admin_code
            request.session['pending_admin_code_expires_at'] = expires_at.isoformat()
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            request.session['pending_admin_next'] = admin_next_path
            request.session.pop('admin_user_id', None)

            try:
                send_mail(
                    subject='Codigo de verificacion de administrador - Agrophia',
                    message=(
                        # Paso de apoyo dentro del flujo principal de la funcionalidad.
                        'Tu codigo de verificacion para iniciar sesion como administrador es: '
                        f'{admin_code}\n\n'
                        'Este codigo expira en 2 minutos.'
                    ),
                    # Actualización de estado intermedio que será utilizada en pasos posteriores.
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[usuario_registro.correo_electronico],
                    fail_silently=False,
                )
            # Control de flujo y validación de condiciones del proceso.
            except Exception:
                request.session.pop('pending_admin_user_id', None)
                request.session.pop('pending_admin_register_id', None)
                request.session.pop('pending_admin_code', None)
                # Paso de apoyo dentro del flujo principal de la funcionalidad.
                request.session.pop('pending_admin_code_expires_at', None)
                logout(request)
                errores['general'] = 'No se pudo enviar el codigo de seguridad al correo del administrador.'
                return render(request, self.template_name, {
                    # Paso de apoyo dentro del flujo principal de la funcionalidad.
                    'errores': errores,
                    'valores': {'username': username}
                })

            return redirect('administrador:admin_verify_code')

        request.session.pop('pending_admin_user_id', None)
        request.session.pop('pending_admin_register_id', None)
        request.session.pop('pending_admin_code', None)
        request.session.pop('pending_admin_code_expires_at', None)
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        request.session.pop('admin_user_id', None)
        # Si no es admin, ir a la vista de usuario
        return redirect("usuarios:home_customer")


def register_step_1(request):
    """Captura y persiste temporalmente los datos del primer paso de registro."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if request.method == "POST":
        documento = request.POST.get("documento", "").strip()
        tdocumento = request.POST.get("tdocumento", "").strip()
        nombres = request.POST.get("nombres", "").strip()
        # Actualización de estado intermedio que será utilizada en pasos posteriores.
        apellidos = request.POST.get("apellidos", "").strip()
        
        # Guardar datos paso 1 en sesión (método estándar Django)
        request.session["register_step_1"] = {
            "tdocumento": tdocumento,
            "documento": documento,
            "nombres": nombres,
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            "apellidos": apellidos,
        }

        # Guardar la foto temporalmente en disco
        if request.FILES.get("foto"):
            foto_file = request.FILES["foto"]
            previous_temp_path = request.session.get("foto_temp_path")
            # Crear carpeta temporal si no existe
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_registros')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Guardar archivo con nombre único para evitar caché del navegador.
            ext = os.path.splitext(foto_file.name)[1]
            temp_filename = f"registro_{documento}_{int(time.time())}{ext}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Guardar archivo
            with open(temp_path, 'wb') as f:
                for chunk in foto_file.chunks():
                    f.write(chunk)

            # Eliminar la foto temporal anterior para no dejar basura en media/temp_registros.
            if previous_temp_path and os.path.exists(previous_temp_path):
                try:
                    os.remove(previous_temp_path)
                except Exception:
                    # Paso de apoyo dentro del flujo principal de la funcionalidad.
                    pass
            
            # Guardar ruta en sesión
            request.session["foto_temp_path"] = temp_path
        elif not request.session.get("foto_temp_path"):
            # Fallback de servidor por si se omite validación en cliente.
            return render(request, "register.html", {
                "valores": request.session.get("register_step_1", {}),
                "has_temp_photo": False,
                "foto_error": "Foto obligatoria.",
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            })

        return redirect("usuarios:register2")

    valores = request.session.get("register_step_1", {})
    foto_temp_path = request.session.get("foto_temp_path")
    has_temp_photo = bool(foto_temp_path and os.path.exists(foto_temp_path))
    foto_preview_url = None
    # Control de flujo y validación de condiciones del proceso.
    if has_temp_photo:
        foto_preview_url = f"{settings.MEDIA_URL}temp_registros/{os.path.basename(foto_temp_path)}"
    foto_preview_version = int(os.path.getmtime(foto_temp_path)) if has_temp_photo else None

    return render(request, "register.html", {
        "valores": valores,
        "has_temp_photo": has_temp_photo,
        "foto_preview_url": foto_preview_url,
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
        "foto_preview_version": foto_preview_version,
    })


def register_step_2(request):
    """Completa el registro creando `User` y `Register` con validaciones."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    valores = request.session.get("register_step_2", {}).copy()
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
        # Actualización de estado intermedio que será utilizada en pasos posteriores.
        departamento = request.POST.get("departamento", "").strip()
        municipio = request.POST.get("municipio", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        # Actualización de estado intermedio que será utilizada en pasos posteriores.
        action = request.POST.get("action", "").strip()
        documento = step1.get("documento", "")

        # Guardar valores para pre-llenar en caso de error
        valores = {
            "email": email,
            "telefono": telefono,
            "departamento": departamento,
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            "municipio": municipio,
            "direccion": direccion,
            "descripcion": descripcion,
        }
        # Persistir datos no sensibles del paso 2 para navegación entre pasos.
        request.session["register_step_2"] = valores

        if action == "back":
            return redirect("usuarios:register")

        # Validar que las contraseñas coincidan
        password_error = _validate_password_policy(password)
        if password_error:
            errores["password"] = password_error
        elif password != confirm:
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
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

        # Validar descripción de perfil
        if len(descripcion) > 120:
            errores["descripcion"] = "La descripción no debe superar 120 caracteres."

        # Si hay errores, retornar a la plantilla con los mensajes
        if errores:
            return render(request, "register2.html", {
                "errores": errores,
                "valores": valores
            # Paso de apoyo dentro del flujo principal de la funcionalidad.
            })

        # Crear usuario Django
        user = User.objects.create_user(
            username=step1["documento"],
            password=password,
            email=email
        # Paso de apoyo dentro del flujo principal de la funcionalidad.
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
            # Actualización de estado intermedio que será utilizada en pasos posteriores.
            nombres=step1["nombres"],
            apellidos=step1["apellidos"],
            correo_electronico=email,
            telefono=telefono,
            # Actualización de estado intermedio que será utilizada en pasos posteriores.
            departamento=departamento,
            municipio=municipio,
            direccion_completa=direccion,
            descripcion_perfil=descripcion,
            # Actualización de estado intermedio que será utilizada en pasos posteriores.
            contrasena=make_password(password),
        )

        # Guardar la foto si existe
        if foto_file:
            register_obj.foto = foto_file
            register_obj.save()

        # Limpiar sesión y archivos temporales
        if "register_step_1" in request.session:
            del request.session["register_step_1"]
        if "register_step_2" in request.session:
            del request.session["register_step_2"]
        # Control de flujo y validación de condiciones del proceso.
        if "foto_temp_path" in request.session:
            foto_temp_path = request.session.get("foto_temp_path")
            del request.session["foto_temp_path"]
            # Eliminar archivo temporal de foto
            if foto_temp_path and os.path.exists(foto_temp_path):
                try:
                    os.remove(foto_temp_path)
                except:
                    # Paso de apoyo dentro del flujo principal de la funcionalidad.
                    pass

        return redirect("usuarios:login")

    return render(request, "register2.html", {"valores": valores, "errores": errores})

def olvidaste_contrasena(request):
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    """Inicia recuperacion de contrasena enviando codigo al correo registrado."""
    # Limpia códigos vencidos para evitar que queden datos obsoletos en BD.
    Register.objects.filter(
        fecha_expiracion_codigo__lt=timezone.now()
    ).update(codigo_reset=None, fecha_expiracion_codigo=None)

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
                    # Paso de apoyo dentro del flujo principal de la funcionalidad.
                    errores["email"] = "No existe una cuenta con este correo."
                
                # Si no hay errores, enviar email
                if not errores:
                    try:
                        send_mail(
                            subject="Código para restablecer contraseña - Agrophia",
                            # Actualización de estado intermedio que será utilizada en pasos posteriores.
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
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    """Valida codigo de recuperacion y actualiza la contrasena del usuario."""
    # Limpia códigos vencidos para evitar que queden datos obsoletos en BD.
    Register.objects.filter(
        fecha_expiracion_codigo__lt=timezone.now()
    ).update(codigo_reset=None, fecha_expiracion_codigo=None)

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
        password_error = _validate_password_policy(password)
        if password_error:
            errores["password"] = password_error

        # CONFIRMAR PASSWORD
        if password != confirm_password:
            errores["confirm_password"] = "Las contraseñas no coinciden."

        # SI TODO OK, verificar código
        if not errores and email_sesion:
            try:
                registro = Register.objects.get(correo_electronico=email_sesion)

                if not registro.codigo_reset:
                    errores["codigo"] = "El codigo no es valido o ya fue utilizado. Solicita uno nuevo."
                
                # Verificar que el código sea correcto
                elif registro.codigo_reset != codigo:
                    errores["codigo"] = "El código es incorrecto."
                
                # Verificar que no haya expirado
                elif not registro.fecha_expiracion_codigo or timezone.now() > registro.fecha_expiracion_codigo:
                    registro.codigo_reset = None
                    registro.fecha_expiracion_codigo = None
                    registro.save(update_fields=["codigo_reset", "fecha_expiracion_codigo"])
                    errores["codigo"] = "El código ha expirado. Solicita uno nuevo."
                
                # Si todo está bien, cambiar la contraseña
                if not errores:
                    # Actualizar contraseña en Register
                    registro.contrasena = make_password(password)
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


# === VISTAS LEGALES Y FAQ ===
from django.views.decorators.http import require_GET

@require_GET
def aviso_privacidad(request):
    """Renderiza la vista legal de aviso de privacidad."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    return render(request, "aviso_privacidad.html")

@require_GET
def terminos_uso(request):
    """Renderiza la vista legal de terminos de uso."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    return render(request, "terminos_uso.html")

@require_GET
def preguntas_frecuentes(request):
    """Renderiza la pagina de preguntas frecuentes."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    return render(request, "preguntas_frecuentes.html")

from django.views.decorators.http import require_POST
from django.http import JsonResponse

@require_POST
def marcar_mensaje_admin_leido(request):
    """Marca como leido un mensaje administrativo del usuario autenticado."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'No autenticado'}, status=403)
    from Mensajes.models import AdminToUserMessage
    from usuarios.models import Register
    register_user = Register.objects.filter(id_usuario=request.user.id).first()
    if not register_user:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)
    mensaje_id = request.POST.get('mensaje_id')
    if not mensaje_id:
        return JsonResponse({'ok': False, 'error': 'ID de mensaje faltante'}, status=400)
    mensaje = AdminToUserMessage.objects.filter(id=mensaje_id, usuario=register_user, leido=False).first()
    if not mensaje:
        return JsonResponse({'ok': False, 'error': 'Mensaje no encontrado'}, status=404)
    mensaje.leido = True
    mensaje.save()
    return JsonResponse({'ok': True})


@require_POST
def enviar_mensaje_admin_usuario_bloqueado(request):
    """Envia al administrador una solicitud desde una cuenta bloqueada."""
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
    token = (request.POST.get('token') or '').strip()
    texto = (request.POST.get('message') or '').strip()

    if not token:
        return JsonResponse({'ok': False, 'error': 'Token no enviado.'}, status=400)

    if len(texto) < 10:
        return JsonResponse({'ok': False, 'error': 'Escribe un mensaje de al menos 10 caracteres.'}, status=400)

    try:
        payload = signing.loads(token, max_age=3600)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Solicitud inválida o expirada.'}, status=400)

    register_id = payload.get('register_id')
    documento = payload.get('documento')
    if not register_id or not documento:
        return JsonResponse({'ok': False, 'error': 'Datos de validación incompletos.'}, status=400)

    usuario_registro = Register.objects.filter(id=register_id, numero_documento=documento).first()
    if not usuario_registro:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado.'}, status=404)

    if usuario_registro.estado in ['activo', 'admin']:
        return JsonResponse({'ok': False, 'error': 'Esta cuenta ya no está bloqueada.'}, status=400)

    sender_user = None
    if usuario_registro.id_usuario:
        sender_user = User.objects.filter(id=usuario_registro.id_usuario).first()
    if sender_user is None:
        sender_user = User.objects.filter(username=usuario_registro.numero_documento).first()
    if sender_user is None:
        sender_user = User.objects.create_user(
            username=usuario_registro.numero_documento,
            password=None,
            email=usuario_registro.correo_electronico,
            first_name=usuario_registro.nombres,
            last_name=usuario_registro.apellidos,
        )

    if usuario_registro.id_usuario != sender_user.id:
        usuario_registro.id_usuario = sender_user.id
        usuario_registro.save(update_fields=['id_usuario'])

    from Mensajes.models import AdminNotification

    AdminNotification.objects.create(
        notification_type=AdminNotification.TYPE_BLOCKED_LOGIN_ATTEMPT,
        sender_user=sender_user,
        sender_register=usuario_registro,
        product=None,
        message=(
            "Mensaje de usuario bloqueado: "
            f"{texto}"
        ),
    )

    return JsonResponse({'ok': True, 'message': 'Tu mensaje fue enviado al administrador.'})

