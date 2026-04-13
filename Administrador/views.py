"""Vistas del panel administrativo de Agrophia (tiendas, productos, usuarios, pedidos y reportes)."""

from django.shortcuts import render, get_object_or_404, redirect
from django import forms
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import csv
from datetime import datetime, timedelta
from reportlab.lib import colors  # pyright: ignore[reportMissingImports]
from reportlab.lib.pagesizes import A4, landscape  # pyright: ignore[reportMissingImports]
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # pyright: ignore[reportMissingImports]
from reportlab.lib.units import cm  # pyright: ignore[reportMissingImports]
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # pyright: ignore[reportMissingImports]
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image  # pyright: ignore[reportMissingImports]
from xml.sax.saxutils import escape
from usuarios.models import Register
from Tiendas.models import Shop
from django.contrib.auth.models import User
from django.core.mail import send_mail

# ============================================================
# GLOSARIO RAPIDO (PALABRAS TECNICAS EN SIMPLE)
# - timestamp: numero que representa una fecha/hora.
#   Sirve para comparar y ordenar fechas mas facil.
# - fromisoformat: convierte texto con formato de fecha (ISO) a datetime.
# - select_related: trae relaciones (FK) en la misma consulta para evitar
#   consultas extra y mejorar rendimiento.
# - in_bulk: trae varios registros de una vez en forma de diccionario
#   {id: objeto}, util para buscar rapido por id.
# - urlsplit / parse_qsl / urlunsplit: utilidades para leer/modificar URLs
#   sin romper sus partes (ruta, query params, fragmento).
# ============================================================

# ============================================================
# BLOQUE 1: GESTION DE TIENDAS (ADMIN)
# Este bloque contiene CRUD y acciones de estado para tiendas, incluyendo validaciones de formulario y relación con propietario.
# ============================================================
from django.views.decorators.http import require_POST

def store_admin_view(request):
    """Renderiza la tabla administrativa de tiendas.

    Args:
        request: Solicitud HTTP del panel admin.

    Returns:
        HttpResponse con la plantilla de listado de tiendas.
    """
    from Administrador.departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
    tiendas = Shop.objects.all().order_by('-created_at')
    return render(request, 'administrador/store_admin.html', {
        'tiendas': tiendas,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
    })

def tienda_admin_detalle_view(request, tienda_id):
    """Muestra el detalle de una tienda y de su propietario asociado.

    Args:
        request: Solicitud HTTP.
        tienda_id: ID de la tienda a consultar.
    """
    tienda = get_object_or_404(Shop, id=tienda_id)
    usuario = tienda.owner if tienda.owner else None
    usuario_info = None
    if usuario:
        usuario_info = Register.objects.filter(id_usuario=usuario.id).order_by('-id').first()
    return render(request, 'administrador/tienda_detalle_admin.html', {
        'tienda': tienda,
        'usuario': usuario,
        'usuario_info': usuario_info,
    })

def tienda_admin_productos_view(request, tienda_id):
    """Muestra el listado de productos de una tienda específica en admin."""
    from Productos.models import Product

    tienda = get_object_or_404(Shop, id=tienda_id)
    productos = (
        Product.objects
        .filter(shop=tienda)
        .select_related('shop')
        .order_by('-created_at')
    )
    return render(request, 'administrador/tienda_productos_admin.html', {
        'tienda': tienda,
        'productos': productos,
    })

def tienda_admin_crear_view(request):
    """Crea una tienda desde administración enlazándola a un cliente existente.

    También prepara datos para autocompletado del formulario.
    """
    from usuarios.models import Register
    success = False
    errores = {}
    valores = {}
    usuarios_con_tienda = Shop.objects.exclude(owner__isnull=True).values_list('owner__id', flat=True)
    usuarios_disponibles = Register.objects.exclude(id_usuario__in=usuarios_con_tienda).exclude(estado='admin').order_by('nombres', 'apellidos')
    usuarios_disponibles_data = [
        {
            'id_usuario': usuario.id_usuario,
            'nombres': usuario.nombres,
            'apellidos': usuario.apellidos,
            'correo_electronico': usuario.correo_electronico,
            'telefono': usuario.telefono,
            'departamento': usuario.departamento,
            'municipio': usuario.municipio,
            'direccion_completa': usuario.direccion_completa,
        }
        for usuario in usuarios_disponibles
    ]

    # Este bloque solo se ejecuta cuando el formulario se envía por POST.
    if request.method == 'POST':
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        import re
        owner_id = request.POST.get('owner_id', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        departamento = request.POST.get('departamento', '').strip()
        municipio = request.POST.get('municipio', '').strip()
        punto_fisico_raw = request.POST.get('punto_fisico', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        horario = request.POST.get('horario', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        valores = {
            'owner_id': owner_id,
            'nombre': nombre,
            'telefono': telefono,
            'email': email,
            'departamento': departamento,
            'municipio': municipio,
            'punto_fisico': punto_fisico_raw,
            'direccion': direccion,
            'horario': horario,
            'descripcion': descripcion,
        }
        propietario = usuarios_disponibles.filter(id_usuario=owner_id).first() if owner_id else None
        owner_user = None
        if not owner_id:
            errores['owner_id'] = 'Debes seleccionar un usuario cliente existente.'
        elif not propietario:
            errores['owner_id'] = 'El usuario seleccionado no esta disponible para crear tienda.'
        else:
            from django.contrib.auth.models import User
            if propietario.id_usuario:
                owner_user = User.objects.filter(id=propietario.id_usuario).first()
            if owner_user is None:
                owner_user = User.objects.filter(username=propietario.numero_documento).first()
            if owner_user is None:
                owner_user = User.objects.create_user(
                    username=propietario.numero_documento,
                    password=None,
                    email=propietario.correo_electronico,
                    first_name=propietario.nombres,
                    last_name=propietario.apellidos,
                )
                owner_user.set_unusable_password()
                owner_user.save(update_fields=['password'])

            if propietario.id_usuario != owner_user.id:
                propietario.id_usuario = owner_user.id
                propietario.save(update_fields=['id_usuario'])
        if not nombre:
            errores['nombre'] = 'El nombre es obligatorio.'
        elif len(nombre) > 50:
            errores['nombre'] = 'El nombre de la tienda no puede superar 50 caracteres.'
        elif not re.fullmatch(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+', nombre):
            errores['nombre'] = 'El nombre de la tienda solo puede contener letras y espacios.'
        if not telefono:
            errores['telefono'] = 'El teléfono es obligatorio.'
        elif not re.fullmatch(r'3\d{9}', telefono):
            errores['telefono'] = 'El teléfono debe tener 10 dígitos y empezar por 3.'
        else:
            owner_phone = (propietario.telefono or '').strip() if propietario else ''
            telefono_owner = owner_phone and owner_phone == telefono
            if not telefono_owner:
                if Register.objects.filter(telefono=telefono).exists():
                    errores['telefono'] = 'El teléfono de la tienda ya está asociado a otro usuario.'
                elif Shop.objects.filter(telefono=telefono).exists():
                    errores['telefono'] = 'El teléfono de la tienda ya está en uso por otra tienda.'
        if not email:
            errores['email'] = 'El correo es obligatorio.'
        else:
            try:
                validate_email(email)
            except ValidationError:
                errores['email'] = 'El correo de la tienda no es válido.'
            else:
                owner_email = (propietario.correo_electronico or '').strip().lower() if propietario else ''
                email_owner = owner_email and owner_email == email.lower()
                if not email_owner:
                    if Register.objects.filter(correo_electronico__iexact=email).exists():
                        errores['email'] = 'El correo de la tienda ya está asociado a otro usuario.'
                    elif Shop.objects.filter(email__iexact=email).exists():
                        errores['email'] = 'El correo de la tienda ya está en uso por otra tienda.'
        if not departamento:
            errores['departamento'] = 'El departamento es obligatorio.'
        if not municipio:
            errores['municipio'] = 'El municipio es obligatorio.'
        if punto_fisico_raw not in ('True', 'False'):
            errores['punto_fisico'] = 'Debes indicar si la tienda tiene punto físico.'
        from .departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
        if departamento and municipio:
            municipios_validos = DEPARTAMENTOS_MUNICIPIOS.get(departamento)
            if municipios_validos and municipio not in municipios_validos:
                errores['municipio'] = f'El municipio "{municipio}" no corresponde al departamento seleccionado.'
        usa_punto_fisico = punto_fisico_raw == 'True'
        if usa_punto_fisico and not direccion:
            errores['direccion'] = 'La dirección es obligatoria si la tienda tiene punto físico.'
        if usa_punto_fisico and not horario:
            errores['horario'] = 'El horario es obligatorio si la tienda tiene punto físico.'
        if usa_punto_fisico and horario:
            from datetime import datetime
            partes_horario = [parte.strip() for parte in horario.split('-')]
            if len(partes_horario) != 2:
                errores['horario'] = 'El horario debe tener formato HH:MM AM/PM - HH:MM AM/PM.'
            else:
                try:
                    apertura_dt = datetime.strptime(partes_horario[0].upper(), '%I:%M %p')
                    cierre_dt = datetime.strptime(partes_horario[1].upper(), '%I:%M %p')
                except ValueError:
                    errores['horario'] = 'El horario debe tener formato HH:MM AM/PM - HH:MM AM/PM.'
                else:
                    if cierre_dt <= apertura_dt:
                        errores['horario'] = 'La hora de cierre debe ser mayor que la de apertura.'
        if punto_fisico_raw == 'False':
            horario = 'No aplica'
            direccion = None
        if not errores:
            Shop.objects.create(
                owner=owner_user,
                nombre=nombre,
                telefono=telefono,
                email=email,
                departamento=departamento,
                municipio=municipio,
                punto_fisico=usa_punto_fisico,
                direccion=direccion,
                horario=horario,
                descripcion=descripcion,
                is_active=True
            )
            success = True
            valores = {}
    from .departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
    return render(request, 'administrador/tienda_crear_admin.html', {
        'success': success,
        'errores': errores,
        'valores': valores,
        'usuarios_disponibles': usuarios_disponibles,
        'usuarios_disponibles_data': usuarios_disponibles_data,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
    })

def tienda_admin_editar_view(request, tienda_id):
    """Edita información de una tienda existente.

    Incluye validación de municipio contra departamento.
    """
    tienda = get_object_or_404(Shop, id=tienda_id)
    usuario_info = Register.objects.filter(id_usuario=tienda.owner_id).order_by('-id').first() if tienda.owner_id else None
    success = False
    errores = {}
    valores = {
        'nombre': tienda.nombre,
        'telefono': tienda.telefono,
        'email': tienda.email,
        'departamento': tienda.departamento,
        'municipio': tienda.municipio,
        'direccion': tienda.direccion,
        'horario': tienda.horario,
        'punto_fisico': 'True' if tienda.punto_fisico else 'False',
        'estado_tienda': 'activa' if tienda.is_active else 'inactiva',
        'descripcion': tienda.descripcion,
        'owner_tipo_documento': usuario_info.tipo_documento if usuario_info else '',
        'owner_numero_documento': usuario_info.numero_documento if usuario_info else '',
        'owner_nombres': usuario_info.nombres if usuario_info else '',
        'owner_apellidos': usuario_info.apellidos if usuario_info else '',
        'owner_correo_electronico': usuario_info.correo_electronico if usuario_info else '',
        'owner_telefono': usuario_info.telefono if usuario_info else '',
        'owner_departamento': usuario_info.departamento if usuario_info else '',
        'owner_municipio': usuario_info.municipio if usuario_info else '',
        'owner_direccion_completa': usuario_info.direccion_completa if usuario_info else '',
    }
    from .departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
    if request.method == 'POST':
        import re
        import unicodedata
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError

        def normalizar_texto(valor):
            """Normaliza texto para comparar valores ignorando tildes y mayúsculas."""
            texto = (valor or '').strip().lower()
            texto = unicodedata.normalize('NFD', texto)
            return ''.join(ch for ch in texto if unicodedata.category(ch) != 'Mn')

        def resolver_valor_catalogo(valor_ingresado, opciones_catalogo):
            """Busca y devuelve el valor oficial del catálogo que coincide con la entrada."""
            if not valor_ingresado or not opciones_catalogo:
                return None
            valor_normalizado = normalizar_texto(valor_ingresado)
            for opcion in opciones_catalogo:
                if normalizar_texto(opcion) == valor_normalizado:
                    return opcion
            return None

        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        departamento = request.POST.get('departamento', '').strip()
        municipio = request.POST.get('municipio', '').strip()
        punto_fisico_raw = request.POST.get('punto_fisico', '').strip()
        estado_tienda = (request.POST.get('estado_tienda', 'activa') or 'activa').strip().lower()
        direccion = request.POST.get('direccion', '').strip()
        horario = request.POST.get('horario', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        owner_tipo_documento = request.POST.get('owner_tipo_documento', '').strip()
        owner_numero_documento = request.POST.get('owner_numero_documento', '').strip()
        owner_nombres = request.POST.get('owner_nombres', '').strip()
        owner_apellidos = request.POST.get('owner_apellidos', '').strip()
        owner_correo_electronico = request.POST.get('owner_correo_electronico', '').strip()
        owner_telefono = request.POST.get('owner_telefono', '').strip()
        owner_departamento = request.POST.get('owner_departamento', '').strip()
        owner_municipio = request.POST.get('owner_municipio', '').strip()
        owner_direccion_completa = request.POST.get('owner_direccion_completa', '').strip()
        owner_foto = request.FILES.get('owner_foto')
        valores = {
            'nombre': nombre,
            'telefono': telefono,
            'email': email,
            'departamento': departamento,
            'municipio': municipio,
            'direccion': direccion,
            'horario': horario,
            'punto_fisico': punto_fisico_raw,
            'estado_tienda': estado_tienda,
            'descripcion': descripcion,
            'owner_tipo_documento': owner_tipo_documento,
            'owner_numero_documento': owner_numero_documento,
            'owner_nombres': owner_nombres,
            'owner_apellidos': owner_apellidos,
            'owner_correo_electronico': owner_correo_electronico,
            'owner_telefono': owner_telefono,
            'owner_departamento': owner_departamento,
            'owner_municipio': owner_municipio,
            'owner_direccion_completa': owner_direccion_completa,
        }
        if not nombre:
            errores['nombre'] = 'El nombre es obligatorio.'
        if not telefono:
            errores['telefono'] = 'El teléfono es obligatorio.'
        elif not re.fullmatch(r'3\d{9}', telefono):
            errores['telefono'] = 'El teléfono debe tener 10 dígitos y empezar por 3.'
        else:
            usuarios_mismo_telefono = Register.objects.exclude(id=usuario_info.id).filter(telefono=telefono) if usuario_info else Register.objects.filter(telefono=telefono)
            if usuarios_mismo_telefono.exists():
                errores['telefono'] = 'El teléfono de la tienda ya está asociado a otro usuario.'
            elif Shop.objects.exclude(id=tienda.id).filter(telefono=telefono).exists():
                errores['telefono'] = 'El teléfono de la tienda ya está en uso por otra tienda.'
        if not email:
            errores['email'] = 'El correo es obligatorio.'
        else:
            try:
                validate_email(email)
            except ValidationError:
                errores['email'] = 'El correo de la tienda no es válido.'
            else:
                owner_email = (usuario_info.correo_electronico or '').strip().lower() if usuario_info else ''
                email_owner = owner_email and owner_email == email.lower()
                if not email_owner:
                    if Register.objects.exclude(id=usuario_info.id).filter(correo_electronico__iexact=email).exists() if usuario_info else Register.objects.filter(correo_electronico__iexact=email).exists():
                        errores['email'] = 'El correo de la tienda ya está asociado a otro usuario.'
                    elif Shop.objects.exclude(id=tienda.id).filter(email__iexact=email).exists():
                        errores['email'] = 'El correo de la tienda ya está en uso por otra tienda.'
        if not departamento:
            errores['departamento'] = 'El departamento es obligatorio.'
        if not municipio:
            errores['municipio'] = 'El municipio es obligatorio.'
        if punto_fisico_raw not in ('True', 'False'):
            errores['punto_fisico'] = 'Debes indicar si la tienda tiene punto físico.'
        if estado_tienda not in ('activa', 'inactiva'):
            errores['estado_tienda'] = 'Debes seleccionar un estado válido para la tienda.'
        from .departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
        if departamento and municipio:
            municipios_validos = DEPARTAMENTOS_MUNICIPIOS.get(departamento)
            municipio_catalogo = resolver_valor_catalogo(municipio, municipios_validos)
            if municipios_validos and not municipio_catalogo:
                errores['municipio'] = f'El municipio "{municipio}" no corresponde al departamento seleccionado.'
            elif municipio_catalogo:
                municipio = municipio_catalogo
                valores['municipio'] = municipio_catalogo

        usa_punto_fisico = punto_fisico_raw == 'True'
        if usa_punto_fisico and not direccion:
            errores['direccion'] = 'La dirección es obligatoria si la tienda tiene punto físico.'
        if usa_punto_fisico and not horario:
            errores['horario'] = 'El horario es obligatorio si la tienda tiene punto físico.'
        if usa_punto_fisico and horario:
            from datetime import datetime
            partes_horario = [parte.strip() for parte in horario.split('-')]
            if len(partes_horario) != 2:
                errores['horario'] = 'El horario debe tener formato HH:MM AM/PM - HH:MM AM/PM.'
            else:
                try:
                    apertura_dt = datetime.strptime(partes_horario[0].upper(), '%I:%M %p')
                    cierre_dt = datetime.strptime(partes_horario[1].upper(), '%I:%M %p')
                except ValueError:
                    errores['horario'] = 'El horario debe tener formato HH:MM AM/PM - HH:MM AM/PM.'
                else:
                    if cierre_dt <= apertura_dt:
                        errores['horario'] = 'La hora de cierre debe ser mayor que la de apertura.'
        if punto_fisico_raw == 'False':
            horario = 'No aplica'
            direccion = None

        if usuario_info:
            if not owner_tipo_documento:
                errores['owner_tipo_documento'] = 'El tipo de documento del propietario es obligatorio.'
            if not owner_numero_documento:
                errores['owner_numero_documento'] = 'El número de documento del propietario es obligatorio.'
            elif not re.fullmatch(r'\d{6,15}', owner_numero_documento):
                errores['owner_numero_documento'] = 'El número de documento debe tener solo dígitos (6 a 15).'
            if not owner_nombres:
                errores['owner_nombres'] = 'Los nombres del propietario son obligatorios.'
            if not owner_apellidos:
                errores['owner_apellidos'] = 'Los apellidos del propietario son obligatorios.'
            if not owner_correo_electronico:
                errores['owner_correo_electronico'] = 'El correo del propietario es obligatorio.'
            else:
                try:
                    validate_email(owner_correo_electronico)
                except ValidationError:
                    errores['owner_correo_electronico'] = 'El correo del propietario no es válido.'
            if not owner_telefono:
                errores['owner_telefono'] = 'El teléfono del propietario es obligatorio.'
            elif not re.fullmatch(r'3\d{9}', owner_telefono):
                errores['owner_telefono'] = 'El teléfono del propietario debe tener 10 dígitos y empezar por 3.'
            if not owner_departamento:
                errores['owner_departamento'] = 'El departamento del propietario es obligatorio.'
            if not owner_municipio:
                errores['owner_municipio'] = 'El municipio del propietario es obligatorio.'
            if not owner_direccion_completa:
                errores['owner_direccion_completa'] = 'La dirección del propietario es obligatoria.'
            if owner_foto and not (owner_foto.content_type or '').startswith('image/'):
                errores['owner_foto'] = 'La foto del propietario debe ser una imagen válida.'

            if owner_departamento and owner_municipio:
                owner_municipios_validos = DEPARTAMENTOS_MUNICIPIOS.get(owner_departamento)
                owner_municipio_catalogo = resolver_valor_catalogo(owner_municipio, owner_municipios_validos)
                if owner_municipios_validos and not owner_municipio_catalogo:
                    errores['owner_municipio'] = f'El municipio "{owner_municipio}" no corresponde al departamento del propietario.'
                elif owner_municipio_catalogo:
                    owner_municipio = owner_municipio_catalogo
                    valores['owner_municipio'] = owner_municipio_catalogo

            if owner_numero_documento:
                usuario_documento = Register.objects.exclude(id=usuario_info.id).filter(numero_documento=owner_numero_documento).first()
                if usuario_documento:
                    nombre_conflicto = f"{usuario_documento.nombres} {usuario_documento.apellidos}".strip() or f"ID {usuario_documento.id}"
                    errores['owner_numero_documento'] = f'El número de documento ya pertenece a {nombre_conflicto}.'

            if owner_correo_electronico:
                usuario_correo = Register.objects.exclude(id=usuario_info.id).filter(correo_electronico=owner_correo_electronico).first()
                if usuario_correo:
                    nombre_conflicto = f"{usuario_correo.nombres} {usuario_correo.apellidos}".strip() or f"ID {usuario_correo.id}"
                    errores['owner_correo_electronico'] = f'El correo ya pertenece a {nombre_conflicto}.'
            if owner_telefono:
                usuario_telefono = Register.objects.exclude(id=usuario_info.id).filter(telefono=owner_telefono).first()
                if usuario_telefono:
                    nombre_conflicto = f"{usuario_telefono.nombres} {usuario_telefono.apellidos}".strip() or f"ID {usuario_telefono.id}"
                    errores['owner_telefono'] = f'El teléfono ya pertenece a {nombre_conflicto}.'

        if not errores:
            tienda.nombre = nombre
            tienda.telefono = telefono
            tienda.email = email
            tienda.departamento = departamento
            tienda.municipio = municipio
            tienda.punto_fisico = usa_punto_fisico
            tienda.is_active = estado_tienda == 'activa'
            tienda.direccion = direccion
            tienda.horario = horario
            tienda.descripcion = descripcion
            tienda.save()

            if usuario_info:
                usuario_info.tipo_documento = owner_tipo_documento
                usuario_info.numero_documento = owner_numero_documento
                usuario_info.nombres = owner_nombres
                usuario_info.apellidos = owner_apellidos
                usuario_info.correo_electronico = owner_correo_electronico
                usuario_info.telefono = owner_telefono
                usuario_info.departamento = owner_departamento
                usuario_info.municipio = owner_municipio
                usuario_info.direccion_completa = owner_direccion_completa
                if owner_foto:
                    usuario_info.foto = owner_foto
                usuario_info.save()

                if tienda.owner_id:
                    owner_user = User.objects.filter(id=tienda.owner_id).first()
                    if owner_user:
                        owner_user.first_name = owner_nombres
                        owner_user.last_name = owner_apellidos
                        owner_user.email = owner_correo_electronico
                        owner_user.save(update_fields=['first_name', 'last_name', 'email'])

            from django.contrib import messages
            from django.shortcuts import redirect
            messages.success(request, 'Tienda editada exitosamente.')
            return redirect('administrador:store_admin')
        return render(request, 'administrador/tienda_editar_admin.html', {
            'errores': errores,
            'valores': valores,
            'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
            'tienda': tienda,
            'usuario_info': usuario_info,
        })
    return render(request, 'administrador/tienda_editar_admin.html', {
        'errores': errores,
        'valores': valores,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
        'tienda': tienda,
        'usuario_info': usuario_info,
    })

@require_POST
def tienda_admin_block_view(request, tienda_id):
    """Bloquea (desactiva) una tienda por ID."""
    tienda = get_object_or_404(Shop, id=tienda_id)
    tienda.is_active = False
    tienda.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})

@require_POST
def tienda_admin_unblock_view(request, tienda_id):
    """Desbloquea (activa) una tienda por ID."""
    tienda = get_object_or_404(Shop, id=tienda_id)
    tienda.is_active = True
    tienda.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})

# ============================================================
# BLOQUE 2: REPORTES DE TIENDAS Y PRODUCTOS
# Reportes PDF de tiendas y productos para administración.
# ============================================================

def reporte_tiendas_view(request):
    """Genera un reporte de tiendas en PDF.

    Soporta dos alcances:
    - general: lista de tiendas con filtros opcionales.
    - individual: ficha de una tienda + historial de actividad.

    Parámetros GET más usados:
    - report_scope, tienda_id
    - nombre, departamento, municipio, estado
    - fields, all_fields
    """
    # Lee alcance del reporte: general (lista) o individual (una tienda).
    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    tienda_id = (request.GET.get('tienda_id') or '').strip()

    # Si el alcance llega inválido, usa el modo seguro por defecto.
    if scope not in {'general', 'individual'}:
        scope = 'general'

    # Si piden modo individual sin ID, vuelve a modo general para evitar error.
    if scope == 'individual' and not tienda_id:
        scope = 'general'

    if scope == 'individual':
        # Carga tienda puntual y su historial para incluir segunda tabla.
        tienda = get_object_or_404(Shop, id=tienda_id)
        history = build_individual_shop_history(tienda)

        # Catálogo de columnas permitidas para impedir claves no soportadas.
        allowed_fields = {
            'id': 'ID',
            'nombre': 'Nombre',
            'telefono': 'Teléfono',
            'correo': 'Correo',
            'departamento': 'Departamento',
            'municipio': 'Municipio',
            'direccion': 'Dirección',
            'horario': 'Horario',
            'estado': 'Estado',
            'fecha_creacion': 'Fecha creación',
        }
        # Valida columnas solicitadas por query param (`fields`).
        selected_fields = resolve_selected_fields(request, allowed_fields)
        headers = [allowed_fields[field] for field in selected_fields]

        # Diccionario base: permite mapear las columnas elegidas al valor real.
        row_payload = {
            'id': tienda.id,
            'nombre': tienda.nombre,
            'telefono': tienda.telefono,
            'correo': tienda.email,
            'departamento': tienda.departamento,
            'municipio': tienda.municipio,
            'direccion': tienda.direccion,
            'horario': tienda.horario,
            'estado': 'Activo' if tienda.is_active else 'Inactivo',
            'fecha_creacion': tienda.created_at.strftime('%Y-%m-%d %H:%M') if tienda.created_at else '',
        }
        # Construye una única fila para el reporte individual.
        rows = [[row_payload.get(field, '') for field in selected_fields]]

        # Encabezados de la segunda tabla (historial de actividad de la tienda).
        history_headers = ['Fecha', 'Área', 'Acción', 'Detalle']
        history_rows = [
            [
                item.get('fecha') or 'Sin fecha',
                item.get('area') or 'General',
                item.get('accion') or 'Actividad',
                item.get('detalle') or '',
            ]
            for item in history
        ]
        # Si no hay actividad, agrega una fila informativa en lugar de dejar vacío.
        if not history_rows:
            history_rows = [['Sin fecha', 'General', 'Sin actividad', 'No se encontraron acciones registradas para esta tienda']]

        # Subtítulo contextual para identificar rápido la tienda exportada.
        subtitle = f"Tienda: {tienda.nombre} (ID {tienda.id})"
        # Renderiza PDF principal + tabla secundaria de actividad.
        return render_generic_report_pdf(
            'Reporte individual de tienda',
            headers,
            rows,
            subtitle=subtitle,
            second_table={
                'title': 'Actividad relacionada con la tienda',
                'headers': history_headers,
                'rows': history_rows,
            },
        )

    # Base del listado general de tiendas.
    tiendas = Shop.objects.all()

    nombre = (request.GET.get('nombre') or '').strip()
    departamento = (request.GET.get('departamento') or '').strip()
    municipio = (request.GET.get('municipio') or '').strip()
    estado = (request.GET.get('estado') or 'todos').strip().lower()

    # Aplica filtros opcionales de búsqueda.
    if nombre:
        tiendas = tiendas.filter(nombre__icontains=nombre)
    if departamento:
        tiendas = tiendas.filter(departamento__icontains=departamento)
    if municipio:
        tiendas = tiendas.filter(municipio__icontains=municipio)
    if estado == 'activo':
        tiendas = tiendas.filter(is_active=True)
    elif estado == 'inactivo':
        tiendas = tiendas.filter(is_active=False)

    # Ordena por fecha de creación descendente (más recientes primero).
    tiendas = tiendas.order_by('-created_at')

    # Catálogo de columnas válidas para el reporte general.
    allowed_fields = {
        'id': 'ID',
        'nombre': 'Nombre',
        'telefono': 'Teléfono',
        'correo': 'Correo',
        'departamento': 'Departamento',
        'municipio': 'Municipio',
        'direccion': 'Dirección',
        'horario': 'Horario',
        'estado': 'Estado',
        'fecha_creacion': 'Fecha creación',
    }
    selected_fields = resolve_selected_fields(request, allowed_fields)
    headers = [allowed_fields[field] for field in selected_fields]

    # Genera filas del reporte general según columnas seleccionadas.
    rows = [
        [
            {
                'id': t.id,
                'nombre': t.nombre,
                'telefono': t.telefono,
                'correo': t.email,
                'departamento': t.departamento,
                'municipio': t.municipio,
                'direccion': t.direccion,
                'horario': t.horario,
                'estado': 'Activo' if t.is_active else 'Inactivo',
                'fecha_creacion': t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else '',
            }.get(field, '')
            for field in selected_fields
        ]
        for t in tiendas
    ]

    # Compone subtítulo con los filtros activos para trazabilidad del reporte.
    filtros = []
    if nombre:
        filtros.append(f"Nombre contiene: {nombre}")
    if departamento:
        filtros.append(f"Departamento: {departamento}")
    if municipio:
        filtros.append(f"Municipio: {municipio}")
    if estado != 'todos':
        filtros.append(f"Estado: {estado}")
    subtitle = ' | '.join(filtros) if filtros else ''

    # Renderiza PDF final del listado general.
    return render_generic_report_pdf('Reporte de tiendas', headers, rows, subtitle=subtitle)


def reporte_productos_view(request):
    """Genera un reporte de productos en PDF.

    Soporta dos alcances:
    - general: listado de productos con filtros.
    - individual: ficha resumida de un producto.

    Parámetros GET más usados:
    - report_scope, producto_id
    - nombre, tipo, unidad, estado
    - fields, all_fields
    """
    from Productos.models import Product
    # Lee alcance del reporte: general o individual.
    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    producto_id = (request.GET.get('producto_id') or '').strip()

    # Si el alcance llega inválido, usa `general` para mantener estabilidad.
    if scope not in {'general', 'individual'}:
        scope = 'general'

    # Si falta ID en modo individual, cae a modo general.
    if scope == 'individual' and not producto_id:
        scope = 'general'

    if scope == 'individual':
        # Carga producto puntual para construir ficha individual.
        producto = get_object_or_404(Product, id=producto_id)

        # Catálogo de columnas permitidas en reporte individual.
        allowed_fields = {
            'id': 'ID',
            'nombre': 'Nombre',
            'tipo': 'Tipo',
            'unidad': 'Unidad',
            'precio': 'Precio',
            'descripcion': 'Descripción',
            'tiempo_durabilidad': 'Tiempo de durabilidad',
            'estado': 'Estado',
            'fecha_creacion': 'Fecha creación',
        }
        # Valida columnas solicitadas por query param (`fields`).
        selected_fields = resolve_selected_fields(request, allowed_fields)
        headers = [allowed_fields[field] for field in selected_fields]

        # Diccionario base para mapear campos seleccionados a su valor.
        row_payload = {
            'id': producto.id,
            'nombre': producto.nombre,
            'tipo': f"{producto.tipo} ({producto.tipo_otro})" if producto.tipo == 'Otros' and producto.tipo_otro else producto.tipo,
            'unidad': producto.unidad,
            'precio': str(producto.precio),
            'descripcion': producto.descripcion,
            'tiempo_durabilidad': producto.tiempo_durabilidad,
            'estado': 'Activo' if producto.is_active else 'Inactivo',
            'fecha_creacion': producto.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(producto, 'created_at') and producto.created_at else '',
        }
        # Construye una única fila para el reporte individual.
        rows = [[row_payload.get(field, '') for field in selected_fields]]

        # Subtítulo contextual para identificar rápido el producto exportado.
        subtitle = f"Producto: {producto.nombre} (ID {producto.id})"
        # Renderiza PDF individual de producto.
        return render_generic_report_pdf('Reporte individual de producto', headers, rows, subtitle=subtitle)

    # Base del listado general de productos.
    productos = Product.objects.all()

    nombre = (request.GET.get('nombre') or '').strip()
    tipo = (request.GET.get('tipo') or '').strip()
    unidad = (request.GET.get('unidad') or '').strip()
    estado = (request.GET.get('estado') or 'todos').strip().lower()

    # Aplica filtros opcionales sobre el queryset.
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if tipo:
        productos = productos.filter(tipo__iexact=tipo)
    if unidad:
        productos = productos.filter(unidad__iexact=unidad)
    if estado == 'activo':
        productos = productos.filter(is_active=True)
    elif estado == 'inactivo':
        productos = productos.filter(is_active=False)

    # Ordena por fecha de creación descendente.
    productos = productos.order_by('-created_at')

    # Catálogo de columnas válidas para el reporte general.
    allowed_fields = {
        'id': 'ID',
        'nombre': 'Nombre',
        'tipo': 'Tipo',
        'unidad': 'Unidad',
        'precio': 'Precio',
        'descripcion': 'Descripción',
        'tiempo_durabilidad': 'Tiempo de durabilidad',
        'estado': 'Estado',
        'fecha_creacion': 'Fecha creación',
    }
    selected_fields = resolve_selected_fields(request, allowed_fields)
    headers = [allowed_fields[field] for field in selected_fields]

    # Genera filas del reporte general según columnas seleccionadas.
    rows = [
        [
            {
                'id': p.id,
                'nombre': p.nombre,
                'tipo': f"{p.tipo} ({p.tipo_otro})" if p.tipo == 'Otros' and p.tipo_otro else p.tipo,
                'unidad': p.unidad,
                'precio': str(p.precio),
                'descripcion': p.descripcion,
                'tiempo_durabilidad': p.tiempo_durabilidad,
                'estado': 'Activo' if p.is_active else 'Inactivo',
                'fecha_creacion': p.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(p, 'created_at') and p.created_at else '',
            }.get(field, '')
            for field in selected_fields
        ]
        for p in productos
    ]

    # Compone subtítulo con los filtros usados en esta exportación.
    filtros = []
    if nombre:
        filtros.append(f"Nombre contiene: {nombre}")
    if tipo:
        filtros.append(f"Tipo: {tipo}")
    if unidad:
        filtros.append(f"Unidad: {unidad}")
    if estado != 'todos':
        filtros.append(f"Estado: {estado}")
    subtitle = ' | '.join(filtros) if filtros else ''

    # Renderiza PDF final del listado general.
    return render_generic_report_pdf('Reporte de productos', headers, rows, subtitle=subtitle)
# ============================================================
# BLOQUE 3: PRODUCTOS (DETALLE / CREACION / EDICION / ESTADO)
# Este bloque administra productos: detalle, creación, edición avanzada de imágenes y bloqueo/desbloqueo.
# ============================================================

def producto_admin_detalle_view(request, product_id):
    """Muestra el detalle administrativo de un producto."""
    from Productos.models import Product
    producto = get_object_or_404(Product, id=product_id)
    return render(request, 'administrador/producto_detalle_admin.html', {'producto': producto})
from Productos.models import Product, ProductImage
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
def producto_admin_crear_view(request):
    """Crea un producto desde el panel admin con validaciones completas.

    Controla:
    - Campos obligatorios.
    - Rango/precio válido.
    - Tipos de imagen permitidos y límite de cantidad.
    """
    success = False
    errores = {}
    valores = {}
    tiendas = Shop.objects.select_related('owner').order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        shop_id = request.POST.get('shop_id', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        tipo_otro = request.POST.get('tipo_otro', '').strip()
        unidad = request.POST.get('unidad', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        tiempo_durabilidad = (request.POST.get('tiempo_durabilidad') or '').strip()
        fotos = request.FILES.getlist('fotos')
        valores = {
            'nombre': nombre,
            'shop_id': shop_id,
            'tipo': tipo,
            'tipo_otro': tipo_otro,
            'unidad': unidad,
            'precio': precio,
            'stock': stock,
            'descripcion': descripcion,
            'tiempo_durabilidad': tiempo_durabilidad,
        }
        if not nombre:
            errores['nombre'] = 'El nombre es obligatorio.'
        tienda = None
        if not shop_id:
            errores['shop'] = 'Debes seleccionar una tienda.'
        else:
            try:
                tienda = Shop.objects.select_related('owner').get(id=int(shop_id))
            except (TypeError, ValueError, Shop.DoesNotExist):
                errores['shop'] = 'La tienda seleccionada no es válida.'
            else:
                if not tienda.owner_id:
                    errores['shop'] = 'La tienda seleccionada no tiene propietario asignado.'
        if not tipo:
            errores['tipo'] = 'El tipo es obligatorio.'
        if tipo == 'Otros' and not tipo_otro:
            errores['tipo_otro'] = 'Debes especificar el tipo.'
        if not unidad:
            errores['unidad'] = 'La unidad es obligatoria.'
        if not precio:
            errores['precio'] = 'El precio es obligatorio.'
        else:
            try:
                precio_val = Decimal(precio)
                if precio_val <= 0:
                    errores['precio'] = 'El precio debe ser mayor que 0.'
            except (InvalidOperation, ValueError):
                errores['precio'] = 'Precio inválido.'
        if not stock:
            errores['stock'] = 'La cantidad disponible es obligatoria.'
        else:
            try:
                stock_val = int(stock)
                if stock_val < 1:
                    errores['stock'] = 'La cantidad disponible debe ser al menos 1.'
            except (TypeError, ValueError):
                errores['stock'] = 'Cantidad disponible inválida.'
        if not descripcion:
            errores['descripcion'] = 'La descripción es obligatoria.'
        if not tiempo_durabilidad:
            errores['tiempo_durabilidad'] = 'El tiempo de durabilidad es obligatorio.'
        if not fotos:
            errores['fotos'] = 'Debes cargar al menos una imagen.'
        elif len(fotos) > 8:
            errores['fotos'] = 'Solo puedes cargar máximo 8 imágenes.'
        else:
            for photo in fotos:
                if not (photo.content_type or '').startswith('image/'):
                    errores['fotos'] = 'Solo se permiten archivos de imagen.'
                    break
        if not errores:
            producto = Product(
                nombre=nombre,
                tipo=tipo,
                tipo_otro=tipo_otro,
                unidad=unidad,
                precio=precio,
                stock=stock,
                descripcion=descripcion,
                is_active=(int(stock) > 0),
                owner=tienda.owner,
                shop=tienda,
            )
            producto.tiempo_durabilidad = tiempo_durabilidad
            try:
                producto.full_clean()
            except ValidationError as exc:
                for field, messages in exc.message_dict.items():
                    errores[field] = messages[0] if messages else 'Valor inválido.'
            else:
                producto.save()
                for photo in fotos:
                    ProductImage.objects.create(product=producto, image=photo)
                from django.contrib import messages
                messages.success(request, 'Producto creado exitosamente.')
                return redirect('administrador:producs_page')
    return render(request, 'administrador/producto_crear_admin.html', {
        'success': success,
        'errores': errores,
        'valores': valores,
        'tiendas': tiendas,
        'tipo_choices': Product.TIPO_CHOICES,
        'unidad_choices': Product.UNIDAD_CHOICES,
    })

def producto_admin_editar_view(request, product_id):
    """Edita un producto existente y gestiona sus imágenes.

    Cómo funciona:
    - Carga el producto y precarga valores para mostrar el formulario.
    - Si llega POST, valida campos de texto, precio, stock y reglas de fotos.
    - Permite borrar imágenes actuales y subir nuevas, manteniendo entre 1 y 8.
    - Si todo es válido, guarda cambios del producto y sincroniza imágenes.
    - Al finalizar, redirige al detalle o al listado según el origen.

    Args:
        request: Solicitud HTTP del panel administrativo.
        product_id: ID del producto a editar.

    Returns:
        HttpResponse: Formulario con errores/valores o redirección por éxito.
    """
    # Busca el producto; si no existe, responde 404 automáticamente.
    producto = get_object_or_404(Product, id=product_id)
    success = False
    errores = {}
    # Valores iniciales para pintar el formulario en GET o tras errores de POST.
    valores = {
        'nombre': producto.nombre,
        'tipo': producto.tipo,
        'tipo_otro': producto.tipo_otro,
        'unidad': producto.unidad,
        'precio': producto.precio,
        'stock': producto.stock,
        'descripcion': producto.descripcion,
        'tiempo_durabilidad': producto.tiempo_durabilidad,
    }
    # Estado de imágenes actuales para controlar límites y UI.
    existing_images = producto.images.all().order_by('-created_at')
    can_upload_more_images = existing_images.count() < 8

    # Procesa edición únicamente cuando el formulario se envía por POST.
    if request.method == 'POST':
        # Lee y limpia campos de formulario.
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        tipo_otro = request.POST.get('tipo_otro', '').strip()
        unidad = request.POST.get('unidad', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        tiempo_durabilidad = (request.POST.get('tiempo_durabilidad') or '').strip()
        # IDs de imágenes marcadas para eliminar + nuevas imágenes subidas.
        delete_image_ids = request.POST.getlist('delete_images')
        new_images = request.FILES.getlist('new_images')

        # Persiste valores enviados para re-renderizar el formulario si hay errores.
        valores = {
            'nombre': nombre,
            'tipo': tipo,
            'tipo_otro': tipo_otro,
            'unidad': unidad,
            'precio': precio,
            'stock': stock,
            'descripcion': descripcion,
            'tiempo_durabilidad': tiempo_durabilidad,
        }

        # Validaciones básicas de negocio del producto.
        if not nombre:
            errores['nombre'] = 'El nombre es obligatorio.'
        if not tipo:
            errores['tipo'] = 'El tipo es obligatorio.'
        if tipo == 'Otros' and not tipo_otro:
            errores['tipo_otro'] = 'Debes especificar el tipo.'
        if not unidad:
            errores['unidad'] = 'La unidad es obligatoria.'
        if not precio:
            errores['precio'] = 'El precio es obligatorio.'
        else:
            try:
                precio_val = Decimal(precio)
                if precio_val <= 0:
                    errores['precio'] = 'El precio debe ser mayor que 0.'
            except (InvalidOperation, ValueError):
                errores['precio'] = 'Precio inválido.'
        if not stock:
            errores['stock'] = 'La cantidad disponible es obligatoria.'
        else:
            try:
                stock_val = int(stock)
                if stock_val < 1:
                    errores['stock'] = 'La cantidad disponible debe ser al menos 1.'
            except (TypeError, ValueError):
                errores['stock'] = 'Cantidad disponible inválida.'
        if not descripcion:
            errores['descripcion'] = 'La descripción es obligatoria.'
        if not tiempo_durabilidad:
            errores['tiempo_durabilidad'] = 'El tiempo de durabilidad es obligatorio.'

        # Valida coherencia de imágenes: al menos 1 y máximo 8 al final del proceso.
        delete_qs = producto.images.filter(id__in=delete_image_ids)
        existing_count = existing_images.count()
        remaining_count = existing_count - delete_qs.count()
        total_after_update = remaining_count + len(new_images)
        if existing_count >= 8 and len(new_images) > 0 and delete_qs.count() == 0:
            errores['fotos'] = 'Ya tienes 8 imágenes. Elimina alguna para poder subir nuevas.'
        elif total_after_update <= 0:
            errores['fotos'] = 'El producto debe tener al menos una imagen.'
        elif total_after_update > 8:
            errores['fotos'] = 'Solo puedes mantener máximo 8 imágenes por producto.'
        else:
            for photo in new_images:
                if not (photo.content_type or '').startswith('image/'):
                    errores['fotos'] = 'Solo se permiten archivos de imagen.'
                    break

        # Si no hay errores de validación, aplica cambios al producto.
        if not errores:
            producto.nombre = nombre
            producto.tipo = tipo
            producto.tipo_otro = tipo_otro
            producto.unidad = unidad
            producto.precio = precio
            producto.stock = stock
            producto.descripcion = descripcion
            producto.tiempo_durabilidad = tiempo_durabilidad
            # Si el stock queda en 0 o menos, fuerza estado inactivo del producto.
            if int(stock) <= 0:
                producto.is_active = False
            try:
                # Ejecuta validaciones de modelo (tipos, constraints y reglas Django).
                producto.full_clean()
            except ValidationError as exc:
                for field, messages in exc.message_dict.items():
                    errores[field] = messages[0] if messages else 'Valor inválido.'
            else:
                producto.save()
                # Elimina imágenes seleccionadas.
                if delete_qs.exists():
                    delete_qs.delete()
                # Crea los nuevos registros de imagen.
                for image_file in new_images:
                    ProductImage.objects.create(product=producto, image=image_file)
                success = True
                # Refresca estado de imágenes para la UI tras guardar.
                existing_images = producto.images.all().order_by('-created_at')
                can_upload_more_images = existing_images.count() < 8

    # Si guardó correctamente, muestra mensaje y redirige según contexto de navegación.
    if success:
        from django.contrib import messages
        messages.success(request, 'Producto editado exitosamente.')
        origen = (request.GET.get('from') or '').strip().lower()
        if origen == 'detail':
            return redirect('administrador:producto_admin_detalle', product_id=producto.id)
        return redirect('administrador:productos_page')

    # Render base (GET) o re-render con errores (POST inválido).
    return render(request, 'administrador/producto_editar_admin.html', {
        'success': success,
        'errores': errores,
        'valores': valores,
        'producto': producto,
        'existing_images': existing_images,
        'can_upload_more_images': can_upload_more_images,
        'tipo_choices': Product.TIPO_CHOICES,
        'unidad_choices': Product.UNIDAD_CHOICES,
    })
from Productos.models import Product
from django.views.decorators.http import require_POST

@require_POST
def producto_admin_block_view(request, product_id):
    """Marca un producto como inactivo."""
    producto = get_object_or_404(Product, id=product_id)
    producto.is_active = False
    producto.disabled_by_admin = True
    producto.save(update_fields=["is_active", "disabled_by_admin"])
    return JsonResponse({'ok': True})

@require_POST
def producto_admin_unblock_view(request, product_id):
    """Marca un producto como activo."""
    producto = get_object_or_404(Product, id=product_id)
    producto.is_active = True
    producto.disabled_by_admin = False
    producto.save(update_fields=["is_active", "disabled_by_admin"])
    return JsonResponse({'ok': True})


def admin_notifications_view(request):
    """Muestra la bandeja de notificaciones del panel administrativo."""
    # Bloque 1: acceso mínimo requerido (usuario autenticado).
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    # Bloque 2: validación de rol. Solo administradores pueden entrar.
    from usuarios.models import Register
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return redirect('usuarios:home_customer')

    # Bloque 3: carga de datos para la bandeja.
    # select_related evita consultas extra al usar remitente/producto en template.
    from Mensajes.models import AdminNotification
    notifications = AdminNotification.objects.select_related(
        'sender_register',
        'sender_user',
        'product',
    ).order_by('-created_at')

    # Bloque 4: render final con las notificaciones más recientes primero.
    return render(request, 'administrador/admin_notifications.html', {
        'notifications': notifications,
    })


@require_POST
def admin_notification_mark_read_view(request, notification_id):
    """Marca como leída una notificación del panel administrativo."""
    # Bloque 1: solo usuarios autenticados pueden ejecutar la acción.
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    # Bloque 2: validación de rol para restringir a administradores.
    from usuarios.models import Register
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return redirect('usuarios:home_customer')

    # Bloque 3: carga de notificación y cambio de estado si aplica.
    from Mensajes.models import AdminNotification
    notification = get_object_or_404(AdminNotification, id=notification_id)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    # Bloque 4: retorno a la bandeja.
    return redirect('administrador:admin_notifications')


@require_POST
def admin_notification_unblock_user_view(request, notification_id):
    """Desbloquea la cuenta reportada en una notificación administrativa.
    Además de reactivar el estado, limpia contadores de bloqueo y
    envía correo de confirmación cuando existe un email válido.
    """
    # Bloque 1: control de autenticación.
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    # Bloque 2: control de autorización (solo admin).
    from usuarios.models import Register
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return redirect('usuarios:home_customer')

    # Bloque 3: carga de notificación y utilidades de correo.
    from Mensajes.models import AdminNotification
    from django.core.mail import send_mail

    notification = get_object_or_404(AdminNotification, id=notification_id)

    # Bloque 4: resolver el usuario objetivo desde la notificación.
    target_register = notification.sender_register
    if target_register is None and notification.sender_user_id:
        target_register = Register.objects.filter(id_usuario=notification.sender_user_id).order_by('-id').first()

    # Si no hay destinatario válido, aborta con mensaje en UI.
    if target_register is None:
        messages.error(request, 'No fue posible identificar el usuario para desbloquear.')
        return redirect('administrador:admin_notifications')

    # Bloque 5: preparar cambios de desbloqueo de forma parcial.
    fields_to_update = []
    if target_register.estado != 'activo':
        target_register.estado = 'activo'
        fields_to_update.append('estado')
    if target_register.failed_login_attempts:
        target_register.failed_login_attempts = 0
        fields_to_update.append('failed_login_attempts')
    if target_register.blocked_until is not None:
        target_register.blocked_until = None
        fields_to_update.append('blocked_until')

    target_email = (target_register.correo_electronico or '').strip()
    target_name = f"{target_register.nombres} {target_register.apellidos}".strip() or 'usuario'

    # Bloque 6: persistir cambios y notificar por correo cuando sea posible.
    if fields_to_update:
        target_register.save(update_fields=fields_to_update)
        email_sent = 0
        if target_email:
            unlock_subject = 'Tu cuenta en Agrophia ha sido desbloqueada'
            unlock_body = (
                f"Hola {target_name},\n\n"
                "Te informamos que tu cuenta en Agrophia ha sido desbloqueada exitosamente por el equipo administrativo.\n\n"
                "Ya puedes volver a iniciar sesión y continuar usando la plataforma con normalidad.\n\n"
                "Si no reconoces esta gestión o necesitas ayuda adicional, responde este correo o contacta nuestro soporte.\n\n"
                "Gracias por confiar en Agrophia.\n"
                "Equipo Agrophia"
            )
            try:
                email_sent = send_mail(
                    unlock_subject,
                    unlock_body,
                    'no-reply@agrophia.com',
                    [target_email],
                    fail_silently=False,
                )
            except Exception:
                email_sent = 0

        if target_email and email_sent <= 0:
            messages.warning(request, 'Usuario desbloqueado, pero no fue posible enviar el correo de notificación.')
        elif not target_email:
            messages.warning(request, 'Usuario desbloqueado, pero no tiene correo registrado para notificar.')
        else:
            messages.success(request, 'Usuario desbloqueado correctamente. Se envió el correo de confirmación.')
    else:
        # No hubo cambios porque ya estaba desbloqueado.
        messages.info(request, 'El usuario ya se encontraba desbloqueado.')

    # Bloque 7: marcar la notificación como leída tras procesarla.
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    # Bloque 8: volver a la bandeja del administrador.
    return redirect('administrador:admin_notifications')


@require_POST
def admin_notification_unblock_product_view(request, notification_id):
    """Desbloquea y habilita un producto reportado en una notificación administrativa."""
    # Bloque 1: control de autenticación.
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    # Bloque 2: control de autorización (solo admin).
    from usuarios.models import Register
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return redirect('usuarios:home_customer')

    # Bloque 3: carga de notificación y validación de tipo esperado.
    from Mensajes.models import AdminNotification
    notification = get_object_or_404(AdminNotification.objects.select_related('product'), id=notification_id)

    if notification.notification_type != AdminNotification.TYPE_PRODUCT_REACTIVATION:
        messages.error(request, 'Esta notificación no corresponde a una solicitud de activación de producto.')
        return redirect('administrador:admin_notifications')

    # Bloque 4: resolver el producto objetivo.
    producto = notification.product
    if producto is None:
        messages.error(request, 'No fue posible identificar el producto asociado a esta notificación.')
        return redirect('administrador:admin_notifications')

    # Bloque 5: desbloquear/habilitar producto si aplica.
    fields_to_update = []
    if not producto.is_active:
        producto.is_active = True
        fields_to_update.append('is_active')
    if producto.disabled_by_admin:
        producto.disabled_by_admin = False
        fields_to_update.append('disabled_by_admin')

    if fields_to_update:
        producto.save(update_fields=fields_to_update)
        messages.success(request, 'Producto desbloqueado y habilitado correctamente.')
    else:
        messages.info(request, 'El producto ya se encontraba habilitado.')

    # Bloque 6: marcar notificación como leída.
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    return redirect('administrador:admin_notifications')


@require_POST
def admin_notification_reply_view(request, notification_id):
    """Responde una notificación y notifica al usuario por correo.

    Guarda copia del mensaje en base de datos (cuando hay Register asociado)
    y luego intenta el envío por email al destinatario resuelto.
    """
    # Bloque 1: validación de sesión activa.
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    # Bloque 2: validación de rol administrativo.
    from usuarios.models import Register
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return redirect('usuarios:home_customer')

    # Bloque 3: carga de modelos necesarios para responder.
    from Mensajes.models import AdminNotification, AdminToUserMessage
    from django.core.mail import send_mail

    notification = get_object_or_404(AdminNotification, id=notification_id)
    reply_text = (request.POST.get('reply_message') or '').strip()

    # La respuesta no puede enviarse vacía.
    if not reply_text:
        messages.error(request, 'Debes escribir una respuesta para enviar.')
        return redirect('administrador:admin_notifications')

    # Bloque 4: resolver destinatario (Register preferido, luego User auth).
    target_register = notification.sender_register
    if target_register is None and notification.sender_user_id:
        target_register = Register.objects.filter(id_usuario=notification.sender_user_id).order_by('-id').first()

    target_email = ''
    target_name = 'usuario'
    if target_register is not None:
        target_email = (target_register.correo_electronico or '').strip()
        target_name = f"{target_register.nombres} {target_register.apellidos}".strip() or 'usuario'
    elif notification.sender_user_id:
        sender_user = notification.sender_user
        if sender_user is not None:
            target_email = (sender_user.email or '').strip()
            target_name = sender_user.get_full_name().strip() or sender_user.username or 'usuario'

    # Si no hay email destino, no se puede completar el envío.
    if not target_email:
        messages.error(request, 'No hay un correo electrónico válido para enviar la respuesta.')
        return redirect('administrador:admin_notifications')

    # Bloque 5: guardar traza interna del mensaje cuando hay Register asociado.
    if target_register is not None:
        AdminToUserMessage.objects.create(
            usuario=target_register,
            texto=reply_text,
            enviado=True,
        )

    # Bloque 6: construir correo saliente al usuario.
    subject = 'Respuesta del administrador de Agrophia'
    email_body = (
        f"Hola {target_name},\n\n"
        "Hemos recibido tu notificación y te respondemos a continuación:\n\n"
        f"{reply_text}\n\n"
        "Mensaje original:\n"
        f"{notification.message}\n\n"
        "Equipo Agrophia"
    )

    # Intento de envío controlado para devolver feedback claro en UI.
    try:
        sent_count = send_mail(
            subject,
            email_body,
            'no-reply@agrophia.com',
            [target_email],
            fail_silently=False,
        )
    except Exception:
        sent_count = 0

    # Si no salió correo, se informa y se corta flujo.
    if sent_count <= 0:
        messages.error(request, 'No se pudo enviar el correo de respuesta. Intenta nuevamente.')
        return redirect('administrador:admin_notifications')

    # Bloque 7: cerrar ciclo marcando notificación como atendida.
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    messages.success(request, 'Respuesta enviada correctamente al correo del usuario.')
    # Bloque 8: volver a la bandeja para continuar gestión.
    return redirect('administrador:admin_notifications')
# ============================================================
# BLOQUE 4: MENSAJERIA ADMINISTRATIVA
# Este bloque gestiona notificaciones del admin y envío de mensajes individuales o masivos a usuarios.
# ============================================================

@require_POST
def usuario_admin_enviar_mensaje_general_view(request):
    """Envía un mensaje masivo a usuarios, tiendas o ambos segmentos.

    El mensaje se registra en AdminToUserMessage y también se intenta enviar por email.
    """
    # Bloque 1: control de acceso (autenticación obligatoria).
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'No autenticado'}, status=403)

    from usuarios.models import Register

    # Bloque 2: autorización de rol (solo admin puede difundir mensajes).
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    # Bloque 3: importaciones locales del flujo de mensajería.
    # json: permite leer el body enviado por fetch/AJAX.
    import json
    # AdminToUserMessage: guarda trazabilidad interna del mensaje enviado.
    from Mensajes.models import AdminToUserMessage
    # Shop: segmenta destinatarios entre usuarios con tienda y sin tienda.
    from Tiendas.models import Shop
    # send_mail: dispara el correo informativo a cada destinatario.
    from django.core.mail import send_mail

    # Bloque 4: parseo del body JSON con fallback seguro.
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    texto = (data.get('mensaje') or '').strip()
    destinatario = data.get('destinatario', 'all')

    if not texto:
        return JsonResponse({'ok': False, 'error': 'Mensaje vacío'}, status=400)

    # Bloque 5: resolución del segmento destino según el selector recibido.
    usuarios = []
    if destinatario == 'all':
        usuarios = list(Register.objects.all())
    elif destinatario == 'users':
        usuarios_con_tienda = Shop.objects.values_list('owner__id', flat=True)
        usuarios = list(Register.objects.exclude(id_usuario__in=usuarios_con_tienda))
    elif destinatario == 'shops':
        usuarios_con_tienda = Shop.objects.values_list('owner__id', flat=True)
        usuarios = list(Register.objects.filter(id_usuario__in=usuarios_con_tienda))
    else:
        return JsonResponse({'ok': False, 'error': 'Destinatario inválido'}, status=400)

    # Bloque 6: persistir copia interna y disparar correo por cada destinatario.
    for usuario in usuarios:
        AdminToUserMessage.objects.create(
            usuario=usuario,
            texto=texto,
            enviado=True
        )
        send_mail(
            'Mensaje importante de Agrophia',
            texto,
            'no-reply@agrophia.com',
            [usuario.correo_electronico],
            fail_silently=True
        )

    # Bloque 7: respuesta resumida para consumo AJAX.
    return JsonResponse({'ok': True, 'enviados': len(usuarios)})
# ============================================================
# BLOQUE 5: PERFIL ADMIN Y FORMULARIO DE USUARIO ADMIN
# Este bloque maneja perfil del administrador y edición/gestión de usuarios con formularios y validaciones.
# ============================================================

from django.contrib.auth.decorators import login_required


def admin_perfil_view(request):
    """Muestra el perfil del administrador autenticado en modo solo lectura."""
    from usuarios.models import Register

    # Bloque 1: el panel requiere sesión admin ya validada.
    admin_id = request.session.get('admin_user_id')
    if not admin_id:
        return redirect('usuarios:login')

    # Bloque 2: carga de perfil y tienda asociada (si existe).
    usuario = get_object_or_404(Register, id_usuario=admin_id)
    tienda = Shop.objects.filter(owner__id=usuario.id_usuario).first()

    # Bloque 3: render en modo detalle/solo lectura.
    return render(
        request,
        'administrador/usuario_detalle_admin.html',
        {
            'usuario': usuario,
            'tienda': tienda,
            'es_perfil_admin': True,
        },
    )


def admin_editar_perfil_view(request):
    """Permite al admin editar su perfil y datos de tienda relacionados."""
    from usuarios.models import Register
    # Bloque 1: validar sesión administrativa activa.
    admin_id = request.session.get('admin_user_id')
    if not admin_id:
        return redirect('usuarios:login')

    # Bloque 2: cargar usuario y tienda para precargar formulario.
    usuario = get_object_or_404(Register, id_usuario=admin_id)
    tienda = Shop.objects.filter(owner__id=usuario.id_usuario).first()

    # Bloque 3: POST guarda cambios de perfil y, opcionalmente, de tienda.
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            if tienda:
                tienda.nombre = request.POST.get('tienda_nombre', tienda.nombre)
                tienda.email = request.POST.get('tienda_email', tienda.email)
                tienda.telefono = request.POST.get('tienda_telefono', tienda.telefono)
                tienda.departamento = request.POST.get('tienda_departamento', tienda.departamento)
                tienda.municipio = request.POST.get('tienda_municipio', tienda.municipio)
                tienda.direccion = request.POST.get('tienda_direccion', tienda.direccion)
                tienda.descripcion = request.POST.get('tienda_descripcion', tienda.descripcion)
                tienda.horario = request.POST.get('tienda_horario', tienda.horario)
                tienda.punto_fisico = request.POST.get('tienda_punto_fisico', 'True') == 'True'
                tienda.is_active = request.POST.get('tienda_is_active', 'True') == 'True'
                tienda.save()
            return redirect('administrador:home_admin')
    else:
        # Bloque 4: GET muestra formulario con valores actuales.
        form = UsuarioAdminForm(instance=usuario)

    # Bloque 5: render final del formulario de edición admin.
    return render(request, 'administrador/usuario_editar_admin.html', {'form': form, 'usuario': usuario, 'tienda': tienda, 'es_perfil_admin': True})

class UsuarioAdminForm(forms.ModelForm):
    """Formulario de edición de perfil de usuario en administración."""
    class Meta:
        """Configura modelo, campos y widgets del formulario admin de usuario."""
        from usuarios.models import Register
        # Modelo base que se editará desde el formulario.
        model = Register
        # Campos habilitados en la edición administrativa.
        fields = [
            'foto', 'tipo_documento', 'numero_documento', 'nombres', 'apellidos',
            'correo_electronico', 'telefono', 'departamento', 'municipio',
            'direccion_completa', 'descripcion_perfil', 'estado'
        ]
        # Widgets personalizados para mejorar la captura en UI.
        widgets = {
            'estado': forms.Select(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')]),
            'descripcion_perfil': forms.Textarea(attrs={'rows': 2, 'maxlength': 100}),
        }

    def clean_correo_electronico(self):
        """Valida unicidad de correo ignorando mayúsculas en edición."""
        # Bloque 1: normalización básica del valor recibido.
        correo = (self.cleaned_data.get('correo_electronico') or '').strip()
        if not correo:
            return correo
        # Bloque 2: evita conflicto con otros registros distintos al actual.
        qs = Register.objects.exclude(id=self.instance.id).filter(correo_electronico__iexact=correo)
        if qs.exists():
            raise forms.ValidationError('Ya existe un usuario con ese correo.')
        return correo

    def clean_telefono(self):
        """Valida que el teléfono no esté duplicado en otro registro."""
        # Bloque 1: limpieza y salida temprana si viene vacío.
        telefono = (self.cleaned_data.get('telefono') or '').strip()
        if not telefono:
            return telefono
        # Bloque 2: validación de duplicado excluyendo la instancia actual.
        qs = Register.objects.exclude(id=self.instance.id).filter(telefono=telefono)
        if qs.exists():
            raise forms.ValidationError('Ya existe un usuario con ese teléfono.')
        return telefono

def usuario_admin_editar_view(request, usuario_id):
    """Edita un usuario y, si aplica, su tienda asociada."""
    from usuarios.models import Register

    # Bloque 1: buscar usuario objetivo por ID interno de Register.
    usuario = get_object_or_404(Register, id=usuario_id)

    # Bloque 2: POST procesa actualización; GET precarga formulario.
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario)
        # Se limita tipo_documento a los valores habilitados en este flujo.
        form.fields['tipo_documento'].choices = [('TI', 'TI'), ('CC', 'CC')]
        form.fields['tipo_documento'].widget = forms.Select(choices=[('TI', 'TI'), ('CC', 'CC')])
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario editado exitosamente.')
            return redirect('administrador:usuario_admin_detalle', usuario_id=usuario.id)
    else:
        form = UsuarioAdminForm(instance=usuario)
        form.fields['tipo_documento'].choices = [('TI', 'TI'), ('CC', 'CC')]
        form.fields['tipo_documento'].widget = forms.Select(choices=[('TI', 'TI'), ('CC', 'CC')])

    # Bloque 3: render del formulario con datos/errores acumulados.
    return render(request, 'administrador/usuario_editar_admin.html', {'form': form, 'usuario': usuario})


@require_POST
def usuario_admin_enviar_recuperacion_view(request, usuario_id):
    """Envía un código temporal de recuperación al correo del usuario."""
    # reverse: construye URLs internas de redirección de forma segura.
    from django.urls import reverse
    # url_has_allowed_host_and_scheme: valida el parámetro `next` para evitar redirecciones inseguras.
    from django.utils.http import url_has_allowed_host_and_scheme
    # settings: toma configuración de correo (ej. DEFAULT_FROM_EMAIL).
    from django.conf import settings
    # validate_email: valida sintaxis básica del correo destino.
    from django.core.validators import validate_email
    # ValidationError: captura errores de validación de email.
    from django.core.exceptions import ValidationError
    # logging: registra fallos de envío para diagnóstico en servidor.
    import logging
    # random + string: generan el código temporal numérico de recuperación.
    import random
    import string
    # Utilidades URL para añadir query params sin romper la ruta original.
    from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

    RECOVERY_CODE_LENGTH = 6
    RECOVERY_CODE_EXPIRY_MINUTES = 15

    logger = logging.getLogger(__name__)

    # Bloque 1: resolver usuario y destino de retorno al finalizar.
    usuario = get_object_or_404(Register, id=usuario_id)
    redirect_url = reverse('administrador:usuario_admin_editar', args=[usuario.id])
    next_url = (request.POST.get('next') or '').strip()
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        redirect_url = next_url

    def with_query_param(url, key, value):
        """Agrega o reemplaza un query param conservando ruta, query y fragmento."""
        partes = urlsplit(url)
        query = dict(parse_qsl(partes.query, keep_blank_values=True))
        query[key] = value
        return urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(query), partes.fragment))

    # Bloque 2: determinar correo de destino (override o correo del usuario).
    correo_override = (request.POST.get('target_email') or '').strip()
    correo_destino = correo_override or (usuario.correo_electronico or '').strip()

    # Bloque 3: validar correo antes de generar y guardar código.
    if not correo_destino:
        return redirect(with_query_param(redirect_url, 'recovery_mail', 'missing_email'))

    try:
        validate_email(correo_destino)
    except ValidationError:
        return redirect(with_query_param(redirect_url, 'recovery_mail', 'missing_email'))

    codigo = ''.join(random.choices(string.digits, k=RECOVERY_CODE_LENGTH))
    usuario.codigo_reset = codigo
    usuario.fecha_expiracion_codigo = timezone.now() + timedelta(minutes=RECOVERY_CODE_EXPIRY_MINUTES)
    usuario.save(update_fields=['codigo_reset', 'fecha_expiracion_codigo'])

    # Bloque 4: enviar correo y mapear resultado a estado para UI.
    try:
        enviados = send_mail(
            subject='Código para restablecer contraseña - Agrophia',
            message=(
                f'Hola {usuario.nombres},\n\n'
                f'Tu código para restablecer la contraseña es: {codigo}\n\n'
                f'Este código es válido por {RECOVERY_CODE_EXPIRY_MINUTES} minutos.\n\n'
                'Si no solicitaste restablecer tu contraseña, ignora este mensaje.\n\n'
                'Saludos,\nEquipo Agrophia'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[correo_destino],
            fail_silently=False,
        )
        if enviados < 1:
            raise RuntimeError('No se pudo confirmar el envío del correo de recuperación.')
    except Exception as exc:
        logger.exception('Fallo enviando correo de recuperación a %s (usuario_id=%s): %s', correo_destino, usuario.id, exc)
        return redirect(with_query_param(redirect_url, 'recovery_mail', 'error'))

    # Bloque 5: confirmación de envío exitoso.
    return redirect(with_query_param(redirect_url, 'recovery_mail', 'sent'))
from django.shortcuts import get_object_or_404

def usuario_admin_detalle_view(request, usuario_id):
    """Renderiza detalle de usuario para consulta administrativa."""
    from usuarios.models import Register

    # Bloque 1: cargar usuario y posible tienda enlazada para la ficha.
    usuario = get_object_or_404(Register, id=usuario_id)
    tienda = Shop.objects.filter(owner__id=usuario.id_usuario).first()

    # Bloque 2: render de la tarjeta de detalle en panel admin.
    return render(request, 'administrador/usuario_detalle_admin.html', {'usuario': usuario, 'tienda': tienda})
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

@never_cache
@ensure_csrf_cookie
def admin_verify_code_view(request):
    """Valida el código temporal de seguridad (2FA) para acceso admin.

    Comprueba expiración, compara el código enviado y, si es válido,
    finaliza el login administrativo habilitando la sesión del panel.
    """
    CODE_LENGTH = 6

    def render_verify_form(error_message=""):
        return render(request, 'administrador/admin_verify_code.html', {
            'remaining_seconds': max(0, int((expires_at - timezone.now()).total_seconds())),
            'form_error': error_message,
        })

    # Bloque 1: recuperar datos temporales guardados durante login admin.
    pending_user_id = request.session.get('pending_admin_user_id')
    pending_register_id = request.session.get('pending_admin_register_id')
    pending_code = request.session.get('pending_admin_code')
    expires_iso = request.session.get('pending_admin_code_expires_at')

    # Si falta contexto de verificación, se obliga a reiniciar autenticación.
    if not pending_user_id or not pending_register_id or not pending_code or not expires_iso:
        messages.error(request, 'Primero debes iniciar sesion como administrador para generar tu codigo de seguridad.')
        return redirect('usuarios:login')

    # Bloque 2: parsear expiración y limpiar sesión si el formato es inválido.
    try:
        expires_at = datetime.fromisoformat(expires_iso)
    except (TypeError, ValueError):
        request.session.pop('pending_admin_user_id', None)
        request.session.pop('pending_admin_register_id', None)
        request.session.pop('pending_admin_code', None)
        request.session.pop('pending_admin_code_expires_at', None)
        messages.error(request, 'El codigo no es valido. Inicia sesion nuevamente.')
        return redirect('usuarios:login')

    # Bloque 3: invalidar códigos vencidos y resetear estado admin temporal.
    if timezone.now() > expires_at:
        reg_expired = Register.objects.filter(id=pending_register_id).first()
        if reg_expired and reg_expired.admin_code_validated:
            reg_expired.admin_code_validated = False
            reg_expired.save(update_fields=['admin_code_validated'])
        request.session.pop('pending_admin_user_id', None)
        request.session.pop('pending_admin_register_id', None)
        request.session.pop('pending_admin_code', None)
        request.session.pop('pending_admin_code_expires_at', None)
        messages.error(request, 'El codigo expiro. Debes iniciar sesion nuevamente.')
        return redirect('usuarios:login')

    # Bloque 4: en POST se valida código y se finaliza el login admin.
    if request.method == 'POST':
        code_input = (request.POST.get('code') or '').strip().upper()
        if len(code_input) != CODE_LENGTH:
            return render_verify_form('El codigo debe tener 6 caracteres.')

        # Comparación directa contra el código temporal almacenado en sesión.
        if code_input != pending_code:
            return render_verify_form('Codigo incorrecto.')

        # Bloque 5: comprobar integridad de usuario auth y perfil admin.
        user = User.objects.filter(id=pending_user_id).first()
        reg = Register.objects.filter(id=pending_register_id, estado='admin').first()
        if not user or not reg:
            request.session.pop('pending_admin_user_id', None)
            request.session.pop('pending_admin_register_id', None)
            request.session.pop('pending_admin_code', None)
            request.session.pop('pending_admin_code_expires_at', None)
            messages.error(request, 'No se pudo validar el administrador.')
            return redirect('usuarios:login')

        # Bloque 6: autenticar sesión definitiva y limpiar datos temporales.
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        request.session['admin_user_id'] = user.id
        reg.admin_code_validated = True
        reg.save(update_fields=['admin_code_validated'])

        request.session.pop('pending_admin_user_id', None)
        request.session.pop('pending_admin_register_id', None)
        request.session.pop('pending_admin_code', None)
        request.session.pop('pending_admin_code_expires_at', None)
        next_admin_path = request.session.pop('pending_admin_next', '/administrador/home/')
        if not next_admin_path.startswith('/administrador/'):
            next_admin_path = '/administrador/home/'

        return redirect(next_admin_path)

    # Bloque 7: GET inicial (o reintento) muestra formulario y cuenta regresiva.
    return render_verify_form()


def admin_logout_view(request):
    """Cierra sesión admin y limpia banderas de validación del código admin."""
    # Bloque 1: obtener sesión admin actual (si existe).
    user_id = request.session.get('admin_user_id')
    if user_id:
        try:
            # Bloque 2: desmarcar validación 2FA en el perfil Register.
            reg = Register.objects.get(id_usuario=user_id)
            reg.admin_code_validated = False
            reg.save()
        except Register.DoesNotExist:
            pass
    # Bloque 3: cerrar sesión auth y limpiar toda la sesión.
    logout(request)
    request.session.flush()
    return redirect('/')

# ============================================================
# BLOQUE 7: UTILIDADES DE ACTIVIDAD Y ORDENAMIENTO
# Este bloque agrupa utilidades para normalizar fechas, ordenar eventos y construir líneas de actividad.
# ============================================================

def safe_fecha(fecha):
    """Devuelve una fecha formateada de manera segura para UI/reportes."""
    # Si es un datetime, intenta convertir a zona local antes de formatear.
    if hasattr(fecha, 'strftime'):
        try:
            fecha_local = timezone.localtime(fecha)
        except Exception:
            fecha_local = fecha
        return fecha_local.strftime('%d/%m/%Y %H:%M')
    return 'Sin fecha'

def activity_category_label(category):
    """Mapea la categoría interna de actividad a una etiqueta visible."""
    # Tabla de traducción para mostrar etiquetas legibles en UI/PDF.
    labels = {
        'all': 'Toda la actividad',
        'users': 'Usuarios',
        'shops': 'Tiendas',
        'products': 'Productos',
        'orders': 'Pedidos',
    }
    return labels.get(category, 'Actividad')

def _activity_timestamp(fecha):
    """Convierte una fecha a número para poder ordenarla fácil.

    En palabras simples: transforma una fecha (datetime) en un número
    comparable. Mientras más grande el número, más reciente la fecha.
    """
    if hasattr(fecha, 'timestamp'):
        return fecha.timestamp()
    return 0

def activity_latest_sort_key(evento):
    """Clave de ordenamiento para eventos del más reciente al más antiguo."""
    # Prioriza eventos con fecha, luego los ordena en descendente.
    fecha = evento.get('occurred_at')
    return (0 if fecha else 1, -_activity_timestamp(fecha), evento.get('sequence', 0))

def activity_first_sort_key(evento):
    """Clave de ordenamiento para eventos del más antiguo al más reciente."""
    # Prioriza eventos con fecha, luego los ordena en ascendente.
    fecha = evento.get('occurred_at')
    return (0 if fecha else 1, _activity_timestamp(fecha), evento.get('sequence', 0))

def build_activity_events():
    """Construye una colección unificada de eventos del sistema."""
    # Bloque 1: estructura base de salida y secuenciador estable.
    eventos = []
    sequence = 0

    # Bloque 2: eventos relacionados con cuentas de usuarios.
    registros = list(Register.objects.exclude(estado='admin').order_by('-id'))
    usuarios_auth = User.objects.in_bulk([
        registro.id_usuario for registro in registros if registro.id_usuario
    ])

    for registro in registros:
        usuario_auth = usuarios_auth.get(registro.id_usuario)
        fecha_registro = getattr(usuario_auth, 'date_joined', None)
        eventos.append({
            'sequence': sequence,
            'occurred_at': fecha_registro,
            'category': 'users',
            'tipo': 'Registro de usuario',
            'descripcion': f"Nuevo usuario registrado: {registro.nombres} {registro.apellidos} ({registro.numero_documento})",
        })
        sequence += 1

        if registro.estado == 'inactivo':
            eventos.append({
                'sequence': sequence,
                'occurred_at': None,
                'category': 'users',
                'tipo': 'Usuario bloqueado',
                'descripcion': f"Usuario bloqueado: {registro.nombres} {registro.apellidos} ({registro.numero_documento})",
            })
            sequence += 1

    # Bloque 3: eventos relacionados con tiendas.
    for tienda in Shop.objects.select_related('owner').order_by('-created_at'):
        propietario = tienda.owner.username if tienda.owner else 'Sin propietario'
        eventos.append({
            'sequence': sequence,
            'occurred_at': tienda.created_at,
            'category': 'shops',
            'tipo': 'Tienda creada',
            'descripcion': f"Nueva tienda creada: {tienda.nombre} (Dueño: {propietario})",
        })
        sequence += 1

        if not tienda.is_active:
            eventos.append({
                'sequence': sequence,
                'occurred_at': None,
                'category': 'shops',
                'tipo': 'Tienda deshabilitada',
                'descripcion': f"Tienda deshabilitada: {tienda.nombre} (Dueño: {propietario})",
            })
            sequence += 1

    # Bloque 4: eventos relacionados con productos.
    for producto in Product.objects.select_related('owner', 'shop').order_by('-created_at'):
        propietario = producto.owner.username if producto.owner else 'Sin propietario'
        eventos.append({
            'sequence': sequence,
            'occurred_at': producto.created_at,
            'category': 'products',
            'tipo': 'Producto creado',
            'descripcion': f"Producto creado: {producto.nombre} (Productor: {propietario})",
        })
        sequence += 1

        if not producto.is_active:
            eventos.append({
                'sequence': sequence,
                'occurred_at': None,
                'category': 'products',
                'tipo': 'Producto deshabilitado',
                'descripcion': f"Producto deshabilitado: {producto.nombre} (ID: {producto.id})",
            })
            sequence += 1

    # Bloque 5: eventos relacionados con pedidos.
    for pedido in Order.objects.select_related('customer').order_by('-created_at'):
        eventos.append({
            'sequence': sequence,
            'occurred_at': pedido.created_at,
            'category': 'orders',
            'tipo': 'Pedido realizado',
            'descripcion': f"Nuevo pedido #{pedido.id} realizado por {pedido.customer.username} por ${pedido.total_amount}",
        })
        sequence += 1

    return eventos

def filter_activity_events(events, category='all', scope='all', count_mode='latest', count_value=100, period='month'):
    """Filtra eventos según criterios de reporte (categoría, alcance y periodo)."""
    # Bloque 1: catálogos de valores aceptados y normalización defensiva.
    valid_categories = {'all', 'users', 'shops', 'products', 'orders'}
    valid_scopes = {'all', 'count', 'period'}
    valid_count_modes = {'latest', 'first'}
    valid_periods = {'month', 'year'}

    if category not in valid_categories:
        category = 'all'
    if scope not in valid_scopes:
        scope = 'all'
    if count_mode not in valid_count_modes:
        count_mode = 'latest'
    if period not in valid_periods:
        period = 'month'

    # Bloque 2: filtro primario por categoría.
    filtrados = [
        evento for evento in events
        if category == 'all' or evento['category'] == category
    ]

    # Bloque 3: alcance por periodo (mes/año actual).
    if scope == 'period':
        ahora = timezone.now()
        if period == 'month':
            filtrados = [
                evento for evento in filtrados
                if evento['occurred_at']
                and evento['occurred_at'].year == ahora.year
                and evento['occurred_at'].month == ahora.month
            ]
        else:
            filtrados = [
                evento for evento in filtrados
                if evento['occurred_at'] and evento['occurred_at'].year == ahora.year
            ]
        return sorted(filtrados, key=activity_latest_sort_key)

    # Bloque 4: alcance por cantidad con modo latest/first.
    if scope == 'count':
        try:
            count = int(count_value)
        except (TypeError, ValueError):
            count = 100
        count = max(1, min(count, 1000))
        sort_key = activity_latest_sort_key if count_mode == 'latest' else activity_first_sort_key
        return sorted(filtrados, key=sort_key)[:count]

    # Bloque 5: alcance total (todo lo disponible).
    return sorted(filtrados, key=activity_latest_sort_key)

def activity_scope_label(scope, count_mode='latest', count_value=100, period='month'):
    """Genera el subtítulo legible del alcance aplicado al reporte."""
    # Traduce parámetros de filtrado a texto legible para subtítulos de reporte.
    if scope == 'count':
        prefix = 'Ultimas' if count_mode == 'latest' else 'Primeras'
        return f"{prefix} {count_value} actividades"
    if scope == 'period':
        return 'Actividades de este mes' if period == 'month' else 'Actividades de este año'
    return 'Toda la actividad disponible'


def resolve_selected_fields(request, allowed_fields, default_fields=None):
    """Valida y resuelve campos seleccionados en reportes dinámicos."""
    # Bloque 1: conjunto de claves permitidas por el reporte.
    allowed_keys = set(allowed_fields.keys())

    # Bloque 2: lectura flexible de `fields` (admite lista y CSV).
    selected = []
    for raw in request.GET.getlist('fields'):
        for chunk in str(raw).split(','):
            key = chunk.strip()
            if key:
                selected.append(key)

    # Bloque 3: selección total cuando aplica flag o no llegan campos.
    all_requested = str(request.GET.get('all_fields', '')).lower() in {'1', 'true', 'on', 'si'}
    if all_requested or not selected:
        selected = list(default_fields or allowed_fields.keys())

    # Bloque 4: depurar claves inválidas y duplicadas preservando orden.
    clean_selected = []
    seen = set()
    for key in selected:
        if key in allowed_keys and key not in seen:
            clean_selected.append(key)
            seen.add(key)

    # Bloque 5: fallback final para nunca devolver una selección vacía.
    if not clean_selected:
        clean_selected = list(default_fields or allowed_fields.keys())

    return clean_selected


def build_individual_user_history(usuario):
    """Construye historial de actividad para un usuario específico."""
    from Pedidos.models import Order, OrderItem
    from Tiendas.models import Shop
    from Productos.models import Product
    from django.contrib.auth.models import User

    # Bloque 1: contexto base del usuario y tipo de cuenta.
    history = []
    auth_user_id = usuario.id_usuario
    auth_user = User.objects.filter(id=auth_user_id).first() if auth_user_id else None

    shops = list(Shop.objects.filter(owner_id=auth_user_id).order_by('-created_at'))
    account_type = 'Tienda' if shops else 'Cliente'

    def add_history(occurred_at, area, action, detail):
        """Registra un evento en el historial del usuario con su contexto."""
        history.append({
            'occurred_at': occurred_at,
            'area': area,
            'accion': action,
            'detalle': detail,
        })

    # Bloque 2: hitos de autenticación/cuenta.
    if auth_user and auth_user.date_joined:
        add_history(
            auth_user.date_joined,
            'Autenticación',
            'Registro de cuenta',
            f"Cuenta creada para {usuario.nombres} {usuario.apellidos}",
        )

    if auth_user and auth_user.last_login:
        add_history(
            auth_user.last_login,
            'Autenticación',
            'Inicio de sesión',
            f"Último inicio de sesión registrado: {safe_fecha(auth_user.last_login)}",
        )

    if usuario.estado == 'inactivo':
        add_history(None, 'Cuenta', 'Cuenta bloqueada', 'Usuario bloqueado por administración')

    # Bloque 3: hitos asociados a tiendas del usuario.
    for tienda in shops:
        add_history(
            tienda.created_at,
            'Tienda',
            'Tienda creada',
            f"Tienda registrada: {tienda.nombre} ({tienda.municipio}, {tienda.departamento})",
        )
        if not tienda.is_active:
            add_history(
                None,
                'Tienda',
                'Tienda deshabilitada',
                f"Tienda deshabilitada: {tienda.nombre}",
            )

    # Bloque 4: actividad de productos publicados por el usuario.
    products = Product.objects.filter(owner_id=auth_user_id).order_by('-created_at')
    for producto in products:
        add_history(
            producto.created_at,
            'Productos',
            'Producto creado',
            f"Producto creado: {producto.nombre} (ID {producto.id})",
        )
        if not producto.is_active:
            motivo = 'deshabilitado por administración' if producto.disabled_by_admin else 'deshabilitado por el usuario'
            add_history(
                None,
                'Productos',
                'Producto deshabilitado',
                f"Producto deshabilitado: {producto.nombre} ({motivo})",
            )

    # Bloque 5: actividad de compras y ventas vinculadas a la cuenta.
    customer_orders = Order.objects.filter(customer_id=auth_user_id).order_by('-created_at')
    for pedido in customer_orders:
        add_history(
            pedido.created_at,
            'Compras',
            'Pedido realizado',
            f"Pedido #{pedido.id} por ${pedido.total_amount} ({pedido.get_status_display()})",
        )

    sale_items = OrderItem.objects.select_related('order', 'product').filter(farmer_id=auth_user_id).order_by('-order__created_at')
    for item in sale_items:
        pedido = item.order
        producto = item.product
        add_history(
            pedido.created_at if pedido else None,
            'Ventas',
            'Venta registrada',
            f"Venta en pedido #{pedido.id if pedido else '-'}: {producto.nombre if producto else 'Producto'} x{item.quantity} (subtotal ${item.subtotal})",
        )

    # Bloque 6: mensajes de ausencia de actividad para mejorar trazabilidad.
    if account_type == 'Cliente' and not customer_orders.exists():
        add_history(None, 'Compras', 'Sin compras registradas', 'No se encontraron pedidos realizados por este usuario')
    if account_type == 'Tienda' and not sale_items.exists():
        add_history(None, 'Ventas', 'Sin ventas registradas', 'No se encontraron ventas asociadas a esta cuenta de tienda')

    # Bloque 7: orden final y formateo de fecha amigable.
    history.sort(key=lambda item: _activity_timestamp(item.get('occurred_at')), reverse=True)

    for item in history:
        item['fecha'] = safe_fecha(item.get('occurred_at'))

    return {
        'account_type': account_type,
        'history': history,
    }


def build_individual_shop_history(tienda):
    """Construye actividad relacionada con una tienda específica."""
    from Pedidos.models import OrderItem
    from Productos.models import Product

    # Bloque 1: acumulador del historial y helper interno.
    history = []

    def add_history(occurred_at, area, action, detail):
        """Agrega una línea de actividad para el historial de la tienda."""
        history.append({
            'occurred_at': occurred_at,
            'area': area,
            'accion': action,
            'detalle': detail,
        })

    # Bloque 2: evento base de creación/estado de la tienda.
    add_history(
        tienda.created_at,
        'Tienda',
        'Tienda creada',
        f"Tienda registrada: {tienda.nombre} ({tienda.municipio}, {tienda.departamento})",
    )

    if not tienda.is_active:
        add_history(None, 'Tienda', 'Tienda deshabilitada', f"Tienda deshabilitada: {tienda.nombre}")

    # Bloque 3: actividad del propietario autenticado.
    owner = getattr(tienda, 'owner', None)
    if owner and owner.date_joined:
        add_history(
            owner.date_joined,
            'Propietario',
            'Cuenta del propietario creada',
            f"Cuenta de {owner.get_full_name().strip() or owner.username} creada",
        )
    if owner and owner.last_login:
        add_history(
            owner.last_login,
            'Propietario',
            'Inicio de sesión del propietario',
            f"Último inicio de sesión: {safe_fecha(owner.last_login)}",
        )

    # Bloque 4: actividad de productos de la tienda.
    products = Product.objects.filter(shop_id=tienda.id).order_by('-created_at')
    for producto in products:
        add_history(
            producto.created_at,
            'Productos',
            'Producto creado',
            f"Producto creado: {producto.nombre} (ID {producto.id})",
        )
        if not producto.is_active:
            motivo = 'deshabilitado por administración' if producto.disabled_by_admin else 'deshabilitado por la tienda'
            add_history(
                None,
                'Productos',
                'Producto deshabilitado',
                f"Producto deshabilitado: {producto.nombre} ({motivo})",
            )

    # Bloque 5: ventas relacionadas con productos de la tienda.
    sale_items = OrderItem.objects.select_related('order', 'product').filter(product__shop_id=tienda.id).order_by('-order__created_at')
    for item in sale_items:
        pedido = item.order
        producto = item.product
        add_history(
            pedido.created_at if pedido else None,
            'Ventas',
            'Venta registrada',
            f"Venta en pedido #{pedido.id if pedido else '-'}: {producto.nombre if producto else 'Producto'} x{item.quantity} (subtotal ${item.subtotal})",
        )

    # Bloque 6: relleno informativo cuando no hay datos.
    if not products.exists():
        add_history(None, 'Productos', 'Sin productos registrados', 'No se encontraron productos asociados a esta tienda')
    if not sale_items.exists():
        add_history(None, 'Ventas', 'Sin ventas registradas', 'No se encontraron ventas asociadas a esta tienda')

    # Bloque 7: ordenamiento final y fecha legible para PDF/UI.
    history.sort(key=lambda item: _activity_timestamp(item.get('occurred_at')), reverse=True)

    for item in history:
        item['fecha'] = safe_fecha(item.get('occurred_at'))

    return history

def render_generic_report_pdf(title, headers, rows, subtitle='', second_table=None):
    """Genera un PDF tabular con estilo para reportes administrativos."""
    class RoundedTable(Table):
        """Table con borde exterior redondeado para estética de comprobante."""

        def __init__(
            self,
            *args,
            round_radius=8,
            stroke_color=colors.HexColor('#D1D5DB'),
            stroke_width=1.1,
            fill_color=None,
            **kwargs,
        ):
            super().__init__(*args, **kwargs)
            self._round_radius = round_radius
            self._stroke_color = stroke_color
            self._stroke_width = stroke_width
            self._fill_color = fill_color

        def draw(self):
            """Dibuja la tabla y aplica borde redondeado personalizado."""
            canv = self.canv
            canv.saveState()
            if self._fill_color is not None:
                canv.setFillColor(self._fill_color)
                canv.setStrokeColor(self._stroke_color)
                canv.setLineWidth(self._stroke_width)
                canv.roundRect(0, 0, self._width, self._height, self._round_radius, stroke=1, fill=1)
            canv.restoreState()

            super().draw()

            if self._fill_color is None and self._stroke_width > 0:
                canv.saveState()
                canv.setStrokeColor(self._stroke_color)
                canv.setLineWidth(self._stroke_width)
                canv.roundRect(0, 0, self._width, self._height, self._round_radius, stroke=1, fill=0)
                canv.restoreState()

    response = HttpResponse(content_type='application/pdf')
    safe_name = title.lower().replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=1.6 * cm,
        leftMargin=1.6 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.6 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        textColor=colors.white,
        spaceAfter=0,
    )
    agrophia_name_style = ParagraphStyle(
        'AgrophiaName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        leading=16,
        textColor=colors.HexColor('#166534'),
        spaceAfter=0,
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=colors.HexColor('#14532D'),
        alignment=TA_CENTER,
    )
    header_cell_style = ParagraphStyle(
        'ReportHeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=9,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        wordWrap='CJK',
    )
    cell_style = ParagraphStyle(
        'ReportCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.4,
        leading=10,
        wordWrap='CJK',
    )

    content_width = doc.width - 0.8 * cm


    # --- LOGO Y NOMBRE AGROPHIA (icono y texto centrados) ---
    elements = []
    try:
        logo_path = 'static/icons/planta.png'
        logo = Image(logo_path, width=1.2 * cm, height=1.2 * cm)
        logo.hAlign = 'CENTER'
        agrophia_name = Paragraph('Agrophia', agrophia_name_style)
        logo_row = Table([[logo, agrophia_name]], colWidths=[1.2 * cm, 3.8 * cm], hAlign='CENTER')
        logo_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (1, 0), (1, 0), 0.21 * cm),  # 8px aprox entre icono y texto
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(logo_row)
    except Exception:
        agrophia_fallback = Paragraph('Agrophia', agrophia_name_style)
        fallback_row = Table([[agrophia_fallback]], colWidths=[5.0 * cm], hAlign='CENTER')
        fallback_row.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 0),
            ('TOPPADDING', (0, 0), (0, 0), 0),
            ('BOTTOMPADDING', (0, 0), (0, 0), 0),
        ]))
        elements.append(fallback_row)
    elements.append(Spacer(1, 0.10 * cm))

    def _cell_to_paragraph(value):
        """Convierte cualquier valor a Paragraph escapando HTML y saltos de línea."""
        text = '' if value is None else str(value)
        return Paragraph(escape(text).replace('\n', '<br/>'), cell_style)

    def _header_to_paragraph(value):
        """Convierte encabezados a Paragraph en mayúsculas y con quiebre visual."""
        text = '' if value is None else str(value).upper()
        return Paragraph(escape(text).replace(' ', '<br/>'), header_cell_style)

    header_box = RoundedTable(
        [[Paragraph(title, title_style)]],
        colWidths=[content_width],
        round_radius=10,
        stroke_color=colors.HexColor('#14532D'),
        stroke_width=1.0,
        fill_color=colors.HexColor('#166534'),
    )
    header_box.hAlign = 'CENTER'
    header_box.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    elements.append(header_box)

    if subtitle:
        elements.append(Spacer(1, 0.2 * cm))
        subtitle_box = RoundedTable(
            [[Paragraph(subtitle, subtitle_style)]],
            colWidths=[content_width],
            round_radius=8,
            stroke_color=colors.HexColor('#BBF7D0'),
            stroke_width=1.0,
            fill_color=colors.HexColor('#ECFDF3'),
        )
        subtitle_box.hAlign = 'CENTER'
        subtitle_box.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(subtitle_box)

    elements.append(Spacer(1, 0.4 * cm))

    def build_data_table(table_headers, table_rows):
        """Construye una tabla PDF con anchos de columna dinámicos."""
        normalized_headers = [str(h).upper() for h in table_headers]
        wrapped_headers = [_header_to_paragraph(h) for h in normalized_headers]
        wrapped_rows = [[_cell_to_paragraph(cell) for cell in row] for row in table_rows]
        data = [wrapped_headers] + wrapped_rows
        column_count = max(1, len(normalized_headers))

        column_weights = []
        for col_idx in range(column_count):
            header_len = len(normalized_headers[col_idx]) if col_idx < len(normalized_headers) else 8
            sample_rows = table_rows[:50]
            max_data_len = 0
            for row in sample_rows:
                if col_idx < len(row):
                    max_data_len = max(max_data_len, len(str(row[col_idx])) if row[col_idx] is not None else 0)
            weight = max(8, min(28, max(header_len, max_data_len // 2)))
            column_weights.append(weight)

        total_weight = sum(column_weights) or 1
        col_widths = [(w / total_weight) * content_width for w in column_weights]

        built_table = RoundedTable(
            data,
            colWidths=col_widths,
            repeatRows=1,
            round_radius=8,
            stroke_color=colors.HexColor('#D1D5DB'),
            stroke_width=1.2,
        )
        built_table.hAlign = 'CENTER'
        built_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F7F7F7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#666666')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7.8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EEF7EE')]),
            ('INNERGRID', (0, 0), (-1, -1), 1.0, colors.HexColor('#D1D5DB')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.2, colors.HexColor('#D1D5DB')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ]))
        return built_table

    elements.append(build_data_table(headers, rows))

    if second_table and second_table.get('headers'):
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#14532D'),
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        section_title = second_table.get('title') or 'Historial'
        section_rows = second_table.get('rows') or [['Sin registros', '', '', '']]

        elements.append(Spacer(1, 0.35 * cm))
        elements.append(Paragraph(escape(str(section_title)), section_title_style))
        elements.append(Spacer(1, 0.12 * cm))
        elements.append(build_data_table(second_table.get('headers', []), section_rows))

    def draw_card_background(canvas, document):
        """Pinta un fondo tipo tarjeta para uniformar el estilo del PDF."""
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#F8FFF9'))
        canvas.roundRect(
            document.leftMargin - 0.25 * cm,
            document.bottomMargin - 0.25 * cm,
            document.width + 0.5 * cm,
            document.height + 0.5 * cm,
            12,
            stroke=0,
            fill=1,
        )
        canvas.restoreState()

    doc.build(elements, onFirstPage=draw_card_background, onLaterPages=draw_card_background)
    return response

# ============================================================
# BLOQUE 8: HOME ADMIN Y REPORTE DE ACTIVIDAD RECIENTE
# Este bloque genera el resumen de actividad en home y el reporte PDF de actividad reciente con filtros.
# ============================================================

def home_admin_view(request):
    """Renderiza el home admin con los últimos eventos de actividad."""
    # Bloque 1: acceso restringido a sesión autenticada.
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    # Bloque 2: validar rol admin y estado de sesión administrativa.
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        logout(request)
        request.session.flush()
        return redirect('usuarios:login')

    if request.session.get('admin_user_id') != request.user.id or not register_admin.admin_code_validated:
        messages.error(request, 'Debes completar la verificacion de seguridad para ingresar al panel.')
        return redirect('administrador:admin_verify_code')

    # Bloque 3: construir resumen de los últimos eventos para el dashboard.
    eventos = [
        {
            'fecha': safe_fecha(evento['occurred_at']),
            'tipo': evento['tipo'],
            'descripcion': evento['descripcion'],
        }
        for evento in filter_activity_events(
            build_activity_events(),
            scope='count',
            count_mode='latest',
            count_value=10,
        )
    ]

    # Bloque 4: render del home con actividad reciente.
    return render(request, 'administrador/home_admin.html', {'eventos': eventos})

def reporte_actividad_reciente_view(request):
    """Genera reporte de actividad reciente en PDF.

    Admite filtros por categoría, alcance, periodo y modo de conteo.
    """
    # Bloque 1: leer filtros de actividad desde query params.
    activity_type = request.GET.get('activity_type', 'all')
    scope = request.GET.get('scope', 'all')
    count_mode = request.GET.get('count_mode', 'latest')
    count_value = request.GET.get('count_value', '100')
    period = request.GET.get('period', 'month')

    # Bloque 2: obtener dataset de eventos según los filtros elegidos.
    eventos = filter_activity_events(
        build_activity_events(),
        category=activity_type,
        scope=scope,
        count_mode=count_mode,
        count_value=count_value,
        period=period,
    )

    # Bloque 3: seleccionar columnas y construir resumen de contexto.
    allowed_fields = {
        'fecha': 'Fecha',
        'categoria': 'Categoria',
        'tipo': 'Tipo',
        'descripcion': 'Descripcion',
    }
    selected_fields = resolve_selected_fields(request, allowed_fields)

    resumen = {
        'tipo_actividad': activity_category_label(activity_type),
        'alcance': activity_scope_label(scope, count_mode, count_value, period),
        'total_resultados': len(eventos),
    }

    # Bloque 4: preparar filas y generar PDF final.
    headers = [allowed_fields[field] for field in selected_fields]
    report_rows = [
        [
            {
                'fecha': safe_fecha(evento['occurred_at']),
                'categoria': activity_category_label(evento['category']),
                'tipo': evento['tipo'],
                'descripcion': evento['descripcion'],
            }.get(field, '')
            for field in selected_fields
        ]
        for evento in eventos
    ]
    subtitle = f"Tipo: {resumen['tipo_actividad']} | Alcance: {resumen['alcance']} | Resultados: {resumen['total_resultados']}"

    return render_generic_report_pdf('Reporte de actividad reciente', headers, report_rows, subtitle=subtitle)

# ============================================================
# BLOQUE 9: USUARIOS, PEDIDOS Y REPORTES ADMIN
# Este bloque centraliza listados, bloqueos, mensajería y reportes administrativos de usuarios/pedidos.
# ============================================================

def usuarios_admin_view(request):
    """Renderiza listado de usuarios administrables (excluye admins)."""
    # Bloque 1: excluir cuentas que ya están asociadas a tiendas.
    from Administrador.departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
    usuarios_con_tienda = Shop.objects.exclude(owner__isnull=True).values_list('owner_id', flat=True)

    # Bloque 2: construir listado de usuarios clientes administrables.
    usuarios = (
        Register.objects
        .exclude(estado='admin')
        .exclude(id_usuario__in=usuarios_con_tienda)
        .order_by('nombres', 'apellidos')
    )

    # Bloque 3: render del panel de usuarios con catálogo geográfico.
    return render(request, 'administrador/usuarios_admin.html', {
        'usuarios': usuarios,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
    })

def orders_page_view(request):
    """Renderiza vista administrativa de pedidos."""
    # Carga pedidos con cliente para evitar consultas extra en template.
    pedidos = Order.objects.select_related('customer').order_by('-created_at')
    return render(request, 'administrador/orders_page.html', {'pedidos': pedidos})

def producs_page_view(request):
    """Renderiza vista administrativa de productos."""
    # Lista productos del más reciente al más antiguo.
    productos = Product.objects.all().order_by('-created_at')
    return render(request, 'administrador/producs_page.html', {'productos': productos})

def usuario_admin_block_view(request, usuario_id):
    """Bloquea un usuario (estado=inactivo) vía endpoint POST."""
    # Bloque 1: endpoint estricto de modificación vía POST.
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    from django.core.mail import send_mail

    # Bloque 2: actualizar estado del usuario y conservar si ya estaba bloqueado.
    usuario = get_object_or_404(Register, id=usuario_id)
    was_blocked = usuario.estado == 'inactivo'
    usuario.estado = 'inactivo'
    usuario.save(update_fields=['estado'])

    # Bloque 3: notificación por correo (si hay email disponible).
    email_sent = 0
    target_email = (usuario.correo_electronico or '').strip()
    if target_email:
        full_name = f"{usuario.nombres} {usuario.apellidos}".strip() or 'usuario'
        subject = 'Tu cuenta en Agrophia ha sido bloqueada temporalmente'
        body = (
            f"Hola {full_name},\n\n"
            "Te informamos que tu cuenta en Agrophia ha sido bloqueada por el equipo administrativo.\n\n"
            "Mientras el bloqueo esté activo, no podrás ingresar ni realizar operaciones en la plataforma.\n"
            "Si consideras que se trata de un error o deseas solicitar revisión, por favor comunícate con soporte o con el administrador.\n\n"
            "Gracias por tu comprensión.\n"
            "Equipo Agrophia"
        )
        try:
            email_sent = send_mail(
                subject,
                body,
                'no-reply@agrophia.com',
                [target_email],
                fail_silently=False,
            )
        except Exception:
            email_sent = 0

    # Bloque 4: respuesta JSON para consumo de frontend/admin.
    return JsonResponse({
        'ok': True,
        'email_sent': bool(email_sent),
        'already_blocked': was_blocked,
    })

def usuario_admin_unblock_view(request, usuario_id):
    """Desbloquea un usuario (estado=activo) vía endpoint POST."""
    # Bloque 1: endpoint estricto de modificación vía POST.
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    from django.core.mail import send_mail

    # Bloque 2: restaurar estado de acceso y limpiar contadores de bloqueo.
    usuario = get_object_or_404(Register, id=usuario_id)
    was_active = usuario.estado == 'activo'
    usuario.estado = 'activo'
    usuario.failed_login_attempts = 0
    usuario.blocked_until = None
    usuario.save(update_fields=['estado', 'failed_login_attempts', 'blocked_until'])

    # Bloque 3: enviar correo de confirmación cuando sea posible.
    email_sent = 0
    target_email = (usuario.correo_electronico or '').strip()
    if target_email:
        full_name = f"{usuario.nombres} {usuario.apellidos}".strip() or 'usuario'
        subject = 'Tu cuenta en Agrophia ha sido desbloqueada'
        body = (
            f"Hola {full_name},\n\n"
            "Te confirmamos que tu cuenta en Agrophia ha sido desbloqueada exitosamente por el equipo administrativo.\n\n"
            "Ya puedes iniciar sesión nuevamente y usar la plataforma con normalidad.\n"
            "Si presentas alguna novedad al ingresar, por favor comunícate con soporte para ayudarte de inmediato.\n\n"
            "Gracias por seguir con nosotros.\n"
            "Equipo Agrophia"
        )
        try:
            email_sent = send_mail(
                subject,
                body,
                'no-reply@agrophia.com',
                [target_email],
                fail_silently=False,
            )
        except Exception:
            email_sent = 0

    # Bloque 4: devolver estado final para feedback en UI.
    return JsonResponse({
        'ok': True,
        'email_sent': bool(email_sent),
        'already_active': was_active,
    })

def usuario_admin_enviar_mensaje_view(request, usuario_id):
    """Envía mensaje administrativo individual a un usuario."""
    # Bloque 1: el endpoint solo acepta POST.
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    import json
    from Mensajes.models import AdminToUserMessage
    from django.core.mail import send_mail

    # Bloque 2: resolver destinatario y parsear body JSON.
    usuario = get_object_or_404(Register, id=usuario_id)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}

    # Bloque 3: validar contenido mínimo del mensaje.
    texto = (data.get('mensaje') or '').strip()
    if not texto:
        return JsonResponse({'ok': False, 'error': 'Mensaje vacío'}, status=400)

    # Bloque 4: guardar traza interna y enviar correo al usuario.
    AdminToUserMessage.objects.create(
        usuario=usuario,
        texto=texto,
        enviado=True,
    )
    send_mail(
        'Mensaje importante de Agrophia',
        texto,
        'no-reply@agrophia.com',
        [usuario.correo_electronico],
        fail_silently=True,
    )

    # Bloque 5: confirmación de operación para frontend.
    return JsonResponse({'ok': True})

def reporte_usuarios_view(request):
    """Genera reporte de usuarios en formato PDF."""
    # Bloque 1: leer alcance del reporte y normalizar entradas.
    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    usuario_id = (request.GET.get('usuario_id') or '').strip()

    if scope not in {'general', 'individual'}:
        scope = 'general'

    if scope == 'individual' and not usuario_id:
        scope = 'general'

    # Bloque 2: reporte individual con ficha y tabla de historial.
    if scope == 'individual':
        usuario = get_object_or_404(Register, id=usuario_id)
        history_payload = build_individual_user_history(usuario)
        account_type = history_payload.get('account_type', 'Cliente')
        history = history_payload.get('history', [])

        allowed_profile_fields = {
            'id': 'ID',
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'tipo_documento': 'Tipo documento',
            'numero_documento': 'Número documento',
            'correo': 'Correo',
            'telefono': 'Teléfono',
            'departamento': 'Departamento',
            'municipio': 'Municipio',
            'direccion': 'Dirección',
            'estado': 'Estado',
            'tipo_cuenta': 'Tipo de cuenta',
        }
        selected_profile_fields = resolve_selected_fields(request, allowed_profile_fields)

        profile_values = {
            'id': usuario.id,
            'nombres': usuario.nombres,
            'apellidos': usuario.apellidos,
            'tipo_documento': usuario.tipo_documento,
            'numero_documento': usuario.numero_documento,
            'correo': usuario.correo_electronico,
            'telefono': usuario.telefono,
            'departamento': usuario.departamento,
            'municipio': usuario.municipio,
            'direccion': usuario.direccion_completa,
            'estado': usuario.estado,
            'tipo_cuenta': account_type,
        }

        headers = [allowed_profile_fields[field] for field in selected_profile_fields]
        rows = [[profile_values.get(field, '') for field in selected_profile_fields]]

        history_headers = ['Fecha', 'Área', 'Acción', 'Detalle']
        history_rows = [
            [
                item.get('fecha') or 'Sin fecha',
                item.get('area') or 'General',
                item.get('accion') or 'Actividad',
                item.get('detalle') or '',
            ]
            for item in history
        ]
        if not history_rows:
            history_rows = [['Sin fecha', 'General', 'Sin actividad', 'No se encontraron acciones registradas para este usuario']]

        subtitle = f"Usuario: {usuario.nombres} {usuario.apellidos} (ID {usuario.id}) | Tipo: {account_type}"

        title = 'Reporte individual de usuario'
        return render_generic_report_pdf(
            title,
            headers,
            rows,
            subtitle=subtitle,
            second_table={
                'title': 'Historial de acciones del usuario',
                'headers': history_headers,
                'rows': history_rows,
            },
        )

    # Bloque 3: reporte general con filtros opcionales.
    usuarios = Register.objects.exclude(estado='admin')

    nombre = (request.GET.get('nombre') or '').strip()
    departamento = (request.GET.get('departamento') or '').strip()
    municipio = (request.GET.get('municipio') or '').strip()
    estado = (request.GET.get('estado') or 'todos').strip().lower()

    if nombre:
        from django.db.models import Q
        usuarios = usuarios.filter(Q(nombres__icontains=nombre) | Q(apellidos__icontains=nombre))
    if departamento:
        usuarios = usuarios.filter(departamento__icontains=departamento)
    if municipio:
        usuarios = usuarios.filter(municipio__icontains=municipio)
    if estado != 'todos':
        usuarios = usuarios.filter(estado__iexact=estado)

    # Bloque 4: columnas dinámicas y armado de filas tabulares.
    usuarios = usuarios.order_by('nombres', 'apellidos')

    allowed_fields = {
        'id': 'ID',
        'nombres': 'Nombres',
        'apellidos': 'Apellidos',
        'tipo_documento': 'Tipo doc.',
        'numero_documento': 'Número doc.',
        'correo': 'Correo',
        'telefono': 'Teléfono',
        'departamento': 'Departamento',
        'municipio': 'Municipio',
        'direccion': 'Dirección',
        'estado': 'Estado',
    }
    selected_fields = resolve_selected_fields(request, allowed_fields)
    headers = [allowed_fields[field] for field in selected_fields]

    rows = [
        [
            {
                'id': u.id,
                'nombres': u.nombres,
                'apellidos': u.apellidos,
                'tipo_documento': u.tipo_documento,
                'numero_documento': u.numero_documento,
                'correo': u.correo_electronico,
                'telefono': u.telefono,
                'departamento': u.departamento,
                'municipio': u.municipio,
                'direccion': u.direccion_completa,
                'estado': u.estado,
            }.get(field, '')
            for field in selected_fields
        ]
        for u in usuarios
    ]

    filtros = []
    if nombre:
        filtros.append(f"Nombre o apellido contiene: {nombre}")
    if departamento:
        filtros.append(f"Departamento: {departamento}")
    if municipio:
        filtros.append(f"Municipio: {municipio}")
    if estado != 'todos':
        filtros.append(f"Estado: {estado}")
    subtitle = ' | '.join(filtros) if filtros else ''

    # Bloque 5: salida final en PDF.
    return render_generic_report_pdf('Reporte de usuarios', headers, rows, subtitle=subtitle)

def usuario_admin_crear_view(request):
    """Crea un usuario desde admin con validaciones de datos y duplicados."""
    from usuarios.models import Register
    from django.contrib.auth.models import User
    from django.contrib.auth.hashers import make_password
    # Bloque 1: estado inicial del formulario y colecciones de errores.
    success = False
    errores = {}
    valores = {}

    # Bloque 2: procesamiento de alta cuando llega POST.
    if request.method == 'POST':
        import re
        from usuarios.views import _validate_password_policy, _validate_person_name
        from Administrador.departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
        nombres = request.POST.get('nombres', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        tipo_documento = request.POST.get('tipo_documento', '').strip()
        numero_documento = request.POST.get('numero_documento', '').strip()
        correo_electronico = request.POST.get('correo_electronico', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        departamento = request.POST.get('departamento', '').strip()
        municipio = request.POST.get('municipio', '').strip()
        direccion_completa = request.POST.get('direccion_completa', '').strip()
        contrasena = request.POST.get('contrasena', '').strip()
        valores = {
            'nombres': nombres,
            'apellidos': apellidos,
            'tipo_documento': tipo_documento,
            'numero_documento': numero_documento,
            'correo_electronico': correo_electronico,
            'telefono': telefono,
            'departamento': departamento,
            'municipio': municipio,
            'direccion_completa': direccion_completa,
        }
        # Bloque 3: validaciones de obligatoriedad, formato y duplicados.
        nombres_error = _validate_person_name(nombres, 'nombre')
        if nombres_error:
            errores['nombres'] = nombres_error

        apellidos_error = _validate_person_name(apellidos, 'apellido')
        if apellidos_error:
            errores['apellidos'] = apellidos_error
        if not tipo_documento:
            errores['tipo_documento'] = 'El tipo de documento es obligatorio.'
        if not numero_documento:
            errores['numero_documento'] = 'El número de documento es obligatorio.'
        elif not re.fullmatch(r'\d{7,10}', numero_documento):
            errores['numero_documento'] = 'El número de documento debe tener entre 7 y 10 dígitos numéricos.'
        elif Register.objects.filter(numero_documento=numero_documento).exists():
            errores['numero_documento'] = 'Ya existe un usuario con ese número de documento.'
        elif User.objects.filter(username=numero_documento).exists():
            errores['numero_documento'] = 'Ya existe un usuario de autenticación con ese número de documento.'
        if not correo_electronico:
            errores['correo_electronico'] = 'El correo es obligatorio.'
        elif Register.objects.filter(correo_electronico__iexact=correo_electronico).exists():
            errores['correo_electronico'] = 'Ya existe un usuario con ese correo.'
        if not telefono:
            errores['telefono'] = 'El teléfono es obligatorio.'
        elif not re.fullmatch(r'3\d{9}', telefono):
            errores['telefono'] = 'El teléfono debe tener 10 dígitos y empezar por 3.'
        elif Register.objects.filter(telefono=telefono).exists():
            errores['telefono'] = 'Ya existe un usuario con ese teléfono.'
        if not departamento:
            errores['departamento'] = 'El departamento es obligatorio.'
        elif departamento not in DEPARTAMENTOS_MUNICIPIOS:
            errores['departamento'] = 'Departamento no válido.'
        if not municipio:
            errores['municipio'] = 'El municipio es obligatorio.'
        elif departamento in DEPARTAMENTOS_MUNICIPIOS and municipio not in DEPARTAMENTOS_MUNICIPIOS[departamento]:
            errores['municipio'] = 'El municipio no corresponde al departamento seleccionado.'
        if not direccion_completa:
            errores['direccion_completa'] = 'La dirección es obligatoria.'
        password_error = _validate_password_policy(contrasena)
        if password_error:
            errores['contrasena'] = password_error

        # Bloque 4: creación de User + Register si no hay errores.
        if not errores:
            user = User.objects.create_user(
                username=numero_documento,
                email=correo_electronico,
                password=contrasena,
                first_name=nombres,
                last_name=apellidos,
            )

            Register.objects.create(
                id_usuario=user.id,
                foto=None,
                nombres=nombres,
                apellidos=apellidos,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                correo_electronico=correo_electronico,
                telefono=telefono,
                departamento=departamento,
                municipio=municipio,
                direccion_completa=direccion_completa,
                contrasena=make_password(contrasena),
                estado='activo'
            )
            success = True
            valores = {}

    # Bloque 5: render final con catálogo de departamentos/municipios.
    from Administrador.departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
    return render(request, 'administrador/usuario_crear_admin.html', {
        'success': success,
        'errores': errores,
        'valores': valores,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS
    })

from Pedidos.models import Order, OrderItem
from django.shortcuts import get_object_or_404, render

# ============================================================
# BLOQUE 10: PEDIDOS (DETALLE / EDICION / REPORTE)
# Este bloque cubre detalle, edición de estado/dirección y generación de reportes PDF de pedidos.
# ============================================================

def pedido_admin_detalle_view(request, pedido_id):
    """Muestra detalle de un pedido y sus ítems asociados."""
    # Bloque 1: cargar pedido por ID y sus ítems relacionados.
    pedido = get_object_or_404(Order, id=pedido_id)
    items = pedido.items.select_related('product', 'farmer').all()

    # Bloque 2: render de detalle administrativo del pedido.
    return render(request, 'administrador/pedido_detalle_card.html', {
        'pedido': pedido,
        'items': items,
    })

def pedido_admin_editar_view(request, pedido_id):
    """Permite editar estado y dirección de entrega de un pedido."""
    # Bloque 1: cargar pedido y preparar contenedor de errores.
    pedido = get_object_or_404(Order, id=pedido_id)
    errores = {}

    # Bloque 2: validar y aplicar cambios cuando llega POST.
    if request.method == 'POST':
        status = request.POST.get('status', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        if status not in dict(Order.STATUS_CHOICES):
            errores['status'] = 'Estado inválido.'
        if not delivery_address:
            errores['delivery_address'] = 'La dirección de entrega es obligatoria.'
        if not errores:
            pedido.status = status
            pedido.delivery_address = delivery_address
            pedido.save()
            from django.contrib import messages
            messages.success(request, 'Pedido actualizado correctamente.')
            return redirect('administrador:orders_page')

    # Bloque 3: re-render con ítems actuales y errores (si existen).
    items = pedido.items.select_related('product', 'farmer').all()
    return render(request, 'administrador/pedido_editar_card.html', {
        'pedido': pedido,
        'items': items,
        'errores': errores,
        'status_choices': Order.STATUS_CHOICES,
    })

def reporte_pedidos_view(request):
    """Genera reporte de pedidos filtrable por estado (PDF)."""
    def format_payment_method(raw_value):
        """Normaliza etiquetas de método de pago para salida consistente."""
        value = (raw_value or '').strip().lower()
        if not value:
            return 'No registrado'
        if 'nequi' in value:
            return 'Nequi'
        if 'tarjet' in value or 'card' in value:
            return 'Tarjeta'
        if 'efectivo' in value or 'cash' in value:
            return 'Efectivo'
        return (raw_value or '').strip()

    def format_delivery_method(raw_value):
        """Normaliza etiquetas de método de entrega para lectura humana."""
        value = (raw_value or '').strip().lower()
        if not value:
            return 'No registrado'
        if 'tienda' in value or 'recog' in value or 'pickup' in value:
            return 'Recoger en tienda'
        if 'domicilio' in value or 'entrega' in value or 'delivery' in value:
            return 'Domicilio'
        return (raw_value or '').strip()

    def format_delivery_address(order_obj):
        """Define qué dirección mostrar según el tipo de entrega del pedido."""
        method = format_delivery_method(order_obj.delivery_method)
        if method == 'Recoger en tienda':
            return 'Recoger en tienda'
        return order_obj.delivery_address or ''

    # Bloque 1: resolver alcance general/individual del reporte.
    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    pedido_id = (request.GET.get('pedido_id') or '').strip()

    if scope not in {'general', 'individual'}:
        scope = 'general'

    if scope == 'individual' and not pedido_id:
        scope = 'general'

    # Bloque 2: salida individual con detalle de ítems del pedido.
    if scope == 'individual':
        pedido = get_object_or_404(Order.objects.select_related('customer'), id=pedido_id)

        allowed_fields = {
            'id': 'ID',
            'cliente': 'Cliente',
            'fecha': 'Fecha',
            'total': 'Total',
            'estado': 'Estado',
            'metodo_pago': 'Método de pago',
            'metodo_entrega': 'Método de entrega',
            'direccion_entrega': 'Dirección de entrega',
        }
        selected_fields = resolve_selected_fields(request, allowed_fields)
        headers = [allowed_fields[field] for field in selected_fields]

        row_payload = {
            'id': pedido.id,
            'cliente': pedido.customer.get_full_name() if hasattr(pedido.customer, 'get_full_name') else pedido.customer.username,
            'fecha': safe_fecha(pedido.created_at),
            'total': str(pedido.total_amount),
            'estado': pedido.get_status_display(),
            'metodo_pago': format_payment_method(pedido.payment_method),
            'metodo_entrega': format_delivery_method(pedido.delivery_method),
            'direccion_entrega': format_delivery_address(pedido),
        }
        rows = [[row_payload.get(field, '') for field in selected_fields]]

        items = pedido.items.select_related('product', 'farmer').all()
        detail_headers = ['Producto', 'Vendedor', 'Cantidad', 'Subtotal']
        detail_rows = [
            [
                item.product.nombre if item.product else '-',
                item.farmer.get_full_name() if item.farmer and hasattr(item.farmer, 'get_full_name') else (item.farmer.username if item.farmer else '-'),
                str(item.quantity),
                str(item.subtotal),
            ]
            for item in items
        ]
        if not detail_rows:
            detail_rows = [['Sin producto', '-', '0', '0']]

        subtitle = f"Pedido: #{pedido.id} | Cliente: {row_payload['cliente']}"
        return render_generic_report_pdf(
            'Reporte individual de pedido',
            headers,
            rows,
            subtitle=subtitle,
            second_table={
                'title': 'Detalle de ítems del pedido',
                'headers': detail_headers,
                'rows': detail_rows,
            },
        )

    # Bloque 3: salida general con filtro por estado.
    estado = request.GET.get('estado', 'todos')
    queryset = Order.objects.select_related('customer').all()
    if estado and estado != 'todos':
        queryset = queryset.filter(status=estado)

    allowed_fields = {
        'id': 'ID',
        'cliente': 'Cliente',
        'fecha': 'Fecha',
        'total': 'Total',
        'estado': 'Estado',
        'metodo_pago': 'Método de pago',
        'metodo_entrega': 'Método de entrega',
        'direccion_entrega': 'Dirección de entrega',
    }
    selected_fields = resolve_selected_fields(request, allowed_fields)
    headers = [allowed_fields[field] for field in selected_fields]

    rows = [
        [
            {
                'id': p.id,
                'cliente': p.customer.get_full_name() if hasattr(p.customer, 'get_full_name') else p.customer.username,
                'fecha': safe_fecha(p.created_at),
                'total': str(p.total_amount),
                'estado': p.get_status_display(),
                'metodo_pago': format_payment_method(p.payment_method),
                'metodo_entrega': format_delivery_method(p.delivery_method),
                'direccion_entrega': format_delivery_address(p),
            }.get(field, '')
            for field in selected_fields
        ]
        for p in queryset.order_by('-created_at')
    ]

    # Bloque 4: generar PDF general con subtítulo del filtro activo.
    subtitle = 'Estado: Todos' if estado == 'todos' else f'Estado: {estado}'
    return render_generic_report_pdf('Reporte de pedidos', headers, rows, subtitle=subtitle)
