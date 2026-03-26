"""
Vistas del panel administrativo de Agrophia.

Este archivo centraliza operaciones de administración para:
- Tiendas
- Productos
- Usuarios
- Pedidos
- Reportes (PDF)
- Actividad reciente

Nota:
El archivo conserva una organización histórica por bloques funcionales.
Los comentarios agregados delimitan secciones y explican flujos críticos.
"""

# ============================================================
# BLOQUE 1: GESTION DE TIENDAS (ADMIN)
# ============================================================
from Tiendas.models import Shop
from django.views.decorators.http import require_POST

def store_admin_view(request):
    """Renderiza la tabla administrativa de tiendas.

    Args:
        request: Solicitud HTTP del panel admin.

    Returns:
        HttpResponse con la plantilla de listado de tiendas.
    """
    # Lista general de tiendas ordenadas por creación reciente.
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
    # Detalle completo de tienda + datos del propietario (si existe).
    tienda = get_object_or_404(Shop, id=tienda_id)
    usuario = tienda.owner if tienda.owner else None
    usuario_info = None
    if usuario:
        usuario_info = Register.objects.filter(id_usuario=usuario.id).first()
    return render(request, 'administrador/tienda_detalle_admin.html', {
        'tienda': tienda,
        'usuario': usuario,
        'usuario_info': usuario_info,
    })

def tienda_admin_crear_view(request):
    """Crea una tienda desde administración enlazándola a un cliente existente.

    También prepara datos para autocompletado del formulario.
    """
    # Crea una tienda enlazándola a un usuario cliente disponible.
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

    if request.method == 'POST':
        owner_id = request.POST.get('owner_id', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        departamento = request.POST.get('departamento', '').strip()
        municipio = request.POST.get('municipio', '').strip()
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
            'direccion': direccion,
            'horario': horario,
            'descripcion': descripcion,
        }
        # Validaciones
        propietario = usuarios_disponibles.filter(id_usuario=owner_id).first() if owner_id else None
        if not owner_id:
            errores['owner_id'] = 'Debes seleccionar un usuario cliente existente.'
        elif not propietario:
            errores['owner_id'] = 'El usuario seleccionado no esta disponible para crear tienda.'
        if not nombre:
            errores['nombre'] = 'El nombre es obligatorio.'
        if not telefono:
            errores['telefono'] = 'El teléfono es obligatorio.'
        if not email:
            errores['email'] = 'El correo es obligatorio.'
        if not departamento:
            errores['departamento'] = 'El departamento es obligatorio.'
        if not municipio:
            errores['municipio'] = 'El municipio es obligatorio.'
        # Validar que el municipio pertenezca al departamento
        from .departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
        if departamento and municipio:
            municipios_validos = DEPARTAMENTOS_MUNICIPIOS.get(departamento)
            if municipios_validos and municipio not in municipios_validos:
                errores['municipio'] = f'El municipio "{municipio}" no corresponde al departamento seleccionado.'
        if not errores:
            Shop.objects.create(
                owner_id=propietario.id_usuario,
                nombre=nombre,
                telefono=telefono,
                email=email,
                departamento=departamento,
                municipio=municipio,
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
    # Edita datos administrativos de tienda con validación básica de ubicación.
    tienda = get_object_or_404(Shop, id=tienda_id)
    usuario_info = Register.objects.filter(id_usuario=tienda.owner_id).first() if tienda.owner_id else None
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
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        email = request.POST.get('email', '').strip()
        departamento = request.POST.get('departamento', '').strip()
        municipio = request.POST.get('municipio', '').strip()
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
        valores = {
            'nombre': nombre,
            'telefono': telefono,
            'email': email,
            'departamento': departamento,
            'municipio': municipio,
            'direccion': direccion,
            'horario': horario,
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
        # Validaciones
        if not nombre:
            errores['nombre'] = 'El nombre es obligatorio.'
        if not telefono:
            errores['telefono'] = 'El teléfono es obligatorio.'
        if not email:
            errores['email'] = 'El correo es obligatorio.'
        if not departamento:
            errores['departamento'] = 'El departamento es obligatorio.'
        if not municipio:
            errores['municipio'] = 'El municipio es obligatorio.'
        # Validar que el municipio pertenezca al departamento
        from .departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
        if departamento and municipio:
            municipios_validos = DEPARTAMENTOS_MUNICIPIOS.get(departamento)
            if municipios_validos and municipio not in municipios_validos:
                errores['municipio'] = f'El municipio "{municipio}" no corresponde al departamento seleccionado.'

        if usuario_info:
            if not owner_tipo_documento:
                errores['owner_tipo_documento'] = 'El tipo de documento del propietario es obligatorio.'
            if not owner_numero_documento:
                errores['owner_numero_documento'] = 'El número de documento del propietario es obligatorio.'
            if not owner_nombres:
                errores['owner_nombres'] = 'Los nombres del propietario son obligatorios.'
            if not owner_apellidos:
                errores['owner_apellidos'] = 'Los apellidos del propietario son obligatorios.'
            if not owner_correo_electronico:
                errores['owner_correo_electronico'] = 'El correo del propietario es obligatorio.'
            if not owner_telefono:
                errores['owner_telefono'] = 'El teléfono del propietario es obligatorio.'
            if not owner_departamento:
                errores['owner_departamento'] = 'El departamento del propietario es obligatorio.'
            if not owner_municipio:
                errores['owner_municipio'] = 'El municipio del propietario es obligatorio.'
            if not owner_direccion_completa:
                errores['owner_direccion_completa'] = 'La dirección del propietario es obligatoria.'

            if owner_departamento and owner_municipio:
                owner_municipios_validos = DEPARTAMENTOS_MUNICIPIOS.get(owner_departamento)
                if owner_municipios_validos and owner_municipio not in owner_municipios_validos:
                    errores['owner_municipio'] = f'El municipio "{owner_municipio}" no corresponde al departamento del propietario.'

            if owner_numero_documento and Register.objects.exclude(id=usuario_info.id).filter(numero_documento=owner_numero_documento).exists():
                errores['owner_numero_documento'] = 'El número de documento ya está en uso.'
            if owner_correo_electronico and Register.objects.exclude(id=usuario_info.id).filter(correo_electronico=owner_correo_electronico).exists():
                errores['owner_correo_electronico'] = 'El correo ya está en uso.'
            if owner_telefono and Register.objects.exclude(id=usuario_info.id).filter(telefono=owner_telefono).exists():
                errores['owner_telefono'] = 'El teléfono ya está en uso.'

        if not errores:
            tienda.nombre = nombre
            tienda.telefono = telefono
            tienda.email = email
            tienda.departamento = departamento
            tienda.municipio = municipio
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
                usuario_info.save()

                if tienda.owner_id:
                    owner_user = User.objects.filter(id=tienda.owner_id).first()
                    if owner_user:
                        owner_user.first_name = owner_nombres
                        owner_user.last_name = owner_apellidos
                        owner_user.email = owner_correo_electronico
                        owner_user.save(update_fields=['first_name', 'last_name', 'email'])

            success = True
        return render(request, 'administrador/tienda_editar_admin.html', {
            'success': success,
            'errores': errores,
            'valores': valores,
            'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
            'tienda': tienda,
            'usuario_info': usuario_info,
        })
    return render(request, 'administrador/tienda_editar_admin.html', {
        'success': success,
        'errores': errores,
        'valores': valores,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
        'tienda': tienda,
        'usuario_info': usuario_info,
    })

@require_POST
def tienda_admin_block_view(request, tienda_id):
    """Bloquea (desactiva) una tienda por ID."""
    # Deshabilita tienda (soft-disable) para ocultarla de flujos activos.
    tienda = get_object_or_404(Shop, id=tienda_id)
    tienda.is_active = False
    tienda.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})

@require_POST
def tienda_admin_unblock_view(request, tienda_id):
    """Desbloquea (activa) una tienda por ID."""
    # Rehabilita tienda previamente bloqueada.
    tienda = get_object_or_404(Shop, id=tienda_id)
    tienda.is_active = True
    tienda.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})

# ============================================================
# BLOQUE 2: REPORTES DE TIENDAS Y PRODUCTOS
# ============================================================

# Reporte de tiendas
def reporte_tiendas_view(request):
    """Genera reporte de tiendas en formato PDF."""
    # Exporta reporte de tiendas en PDF.
    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    tienda_id = (request.GET.get('tienda_id') or '').strip()

    if scope not in {'general', 'individual'}:
        scope = 'general'

    if scope == 'individual' and not tienda_id:
        scope = 'general'

    if scope == 'individual':
        tienda = get_object_or_404(Shop, id=tienda_id)
        history = build_individual_shop_history(tienda)

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
        rows = [[row_payload.get(field, '') for field in selected_fields]]

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
            history_rows = [['Sin fecha', 'General', 'Sin actividad', 'No se encontraron acciones registradas para esta tienda']]

        subtitle = f"Tienda: {tienda.nombre} (ID {tienda.id})"
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

    tiendas = Shop.objects.all()

    nombre = (request.GET.get('nombre') or '').strip()
    departamento = (request.GET.get('departamento') or '').strip()
    municipio = (request.GET.get('municipio') or '').strip()
    estado = (request.GET.get('estado') or 'todos').strip().lower()

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

    tiendas = tiendas.order_by('-created_at')

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

    return render_generic_report_pdf('Reporte de tiendas', headers, rows, subtitle=subtitle)
# Reporte de productos
def reporte_productos_view(request):
    """Genera reporte de productos en formato PDF."""
    # Exporta reporte de productos en PDF.
    from Productos.models import Product
    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    producto_id = (request.GET.get('producto_id') or '').strip()

    if scope not in {'general', 'individual'}:
        scope = 'general'

    if scope == 'individual' and not producto_id:
        scope = 'general'

    if scope == 'individual':
        producto = get_object_or_404(Product, id=producto_id)

        allowed_fields = {
            'id': 'ID',
            'nombre': 'Nombre',
            'tipo': 'Tipo',
            'unidad': 'Unidad',
            'precio': 'Precio',
            'descripcion': 'Descripción',
            'garantia': 'Garantía',
            'estado': 'Estado',
            'fecha_creacion': 'Fecha creación',
        }
        # Respeta los campos seleccionados desde el formulario tambien
        # para el reporte individual de producto.
        selected_fields = resolve_selected_fields(request, allowed_fields)
        headers = [allowed_fields[field] for field in selected_fields]

        row_payload = {
            'id': producto.id,
            'nombre': producto.nombre,
            'tipo': f"{producto.tipo} ({producto.tipo_otro})" if producto.tipo == 'Otros' and producto.tipo_otro else producto.tipo,
            'unidad': producto.unidad,
            'precio': str(producto.precio),
            'descripcion': producto.descripcion,
            'garantia': producto.garantia,
            'estado': 'Activo' if producto.is_active else 'Inactivo',
            'fecha_creacion': producto.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(producto, 'created_at') and producto.created_at else '',
        }
        rows = [[row_payload.get(field, '') for field in selected_fields]]

        subtitle = f"Producto: {producto.nombre} (ID {producto.id})"
        return render_generic_report_pdf('Reporte individual de producto', headers, rows, subtitle=subtitle)

    productos = Product.objects.all()

    nombre = (request.GET.get('nombre') or '').strip()
    tipo = (request.GET.get('tipo') or '').strip()
    unidad = (request.GET.get('unidad') or '').strip()
    estado = (request.GET.get('estado') or 'todos').strip().lower()

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

    productos = productos.order_by('-created_at')

    allowed_fields = {
        'id': 'ID',
        'nombre': 'Nombre',
        'tipo': 'Tipo',
        'unidad': 'Unidad',
        'precio': 'Precio',
        'descripcion': 'Descripción',
        'garantia': 'Garantía',
        'estado': 'Estado',
        'fecha_creacion': 'Fecha creación',
    }
    selected_fields = resolve_selected_fields(request, allowed_fields)
    headers = [allowed_fields[field] for field in selected_fields]

    rows = [
        [
            {
                'id': p.id,
                'nombre': p.nombre,
                'tipo': f"{p.tipo} ({p.tipo_otro})" if p.tipo == 'Otros' and p.tipo_otro else p.tipo,
                'unidad': p.unidad,
                'precio': str(p.precio),
                'descripcion': p.descripcion,
                'garantia': p.garantia,
                'estado': 'Activo' if p.is_active else 'Inactivo',
                'fecha_creacion': p.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(p, 'created_at') and p.created_at else '',
            }.get(field, '')
            for field in selected_fields
        ]
        for p in productos
    ]

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

    return render_generic_report_pdf('Reporte de productos', headers, rows, subtitle=subtitle)
# ============================================================
# BLOQUE 3: PRODUCTOS (DETALLE / CREACION / EDICION / ESTADO)
# ============================================================

# Vista detalle producto admin
def producto_admin_detalle_view(request, product_id):
    """Muestra el detalle administrativo de un producto."""
    # Muestra ficha detallada del producto para revisión administrativa.
    from Productos.models import Product
    producto = get_object_or_404(Product, id=product_id)
    return render(request, 'administrador/producto_detalle_admin.html', {'producto': producto})
from Productos.models import Product, ProductImage
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
# --- Vistas para crear y editar productos desde el admin ---
def producto_admin_crear_view(request):
    """Crea un producto desde el panel admin con validaciones completas.

    Controla:
    - Campos obligatorios.
    - Rango/precio válido.
    - Tipos de imagen permitidos y límite de cantidad.
    """
    # Alta administrativa de producto con validaciones de contenido e imágenes.
    success = False
    errores = {}
    valores = {}
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        tipo_otro = request.POST.get('tipo_otro', '').strip()
        unidad = request.POST.get('unidad', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        garantia = request.POST.get('garantia', '').strip()
        fotos = request.FILES.getlist('fotos')
        valores = {
            'nombre': nombre,
            'tipo': tipo,
            'tipo_otro': tipo_otro,
            'unidad': unidad,
            'precio': precio,
            'stock': stock,
            'descripcion': descripcion,
            'garantia': garantia,
        }
        # Validaciones básicas
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
        if not garantia:
            errores['garantia'] = 'La garantía es obligatoria.'
        if not fotos:
            errores['fotos'] = 'Debes cargar al menos una imagen.'
        elif len(fotos) > 8:
            errores['fotos'] = 'Solo puedes cargar máximo 8 imágenes.'
        else:
            for photo in fotos:
                if not (photo.content_type or '').startswith('image/'):
                    errores['fotos'] = 'Solo se permiten archivos de imagen.'
                    break
        # Validación de modelo
        if not errores:
            producto = Product(
                nombre=nombre,
                tipo=tipo,
                tipo_otro=tipo_otro,
                unidad=unidad,
                precio=precio,
                stock=stock,
                descripcion=descripcion,
                garantia=garantia,
                is_active=(int(stock) > 0),
                owner=request.user if request.user.is_authenticated else None
            )
            try:
                producto.full_clean()
            except ValidationError as exc:
                for field, messages in exc.message_dict.items():
                    errores[field] = messages[0] if messages else 'Valor inválido.'
            else:
                producto.save()
                for photo in fotos:
                    ProductImage.objects.create(product=producto, image=photo)
                success = True
                valores = {}
    return render(request, 'administrador/producto_crear_admin.html', {
        'success': success,
        'errores': errores,
        'valores': valores,
        'tipo_choices': Product.TIPO_CHOICES,
        'unidad_choices': Product.UNIDAD_CHOICES,
    })

def producto_admin_editar_view(request, product_id):
    """Edita un producto y administra sus imágenes asociadas.

    Permite eliminar imágenes actuales y cargar nuevas respetando límites.
    """
    # Edición administrativa con control de imágenes (máximo y mínimos permitidos).
    producto = get_object_or_404(Product, id=product_id)
    success = False
    errores = {}
    valores = {
        'nombre': producto.nombre,
        'tipo': producto.tipo,
        'tipo_otro': producto.tipo_otro,
        'unidad': producto.unidad,
        'precio': producto.precio,
        'stock': producto.stock,
        'descripcion': producto.descripcion,
        'garantia': producto.garantia,
    }
    existing_images = producto.images.all().order_by('-created_at')
    can_upload_more_images = existing_images.count() < 8
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        tipo_otro = request.POST.get('tipo_otro', '').strip()
        unidad = request.POST.get('unidad', '').strip()
        precio = request.POST.get('precio', '').strip()
        stock = request.POST.get('stock', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        garantia = request.POST.get('garantia', '').strip()
        # método de pago y entrega eliminados
        delete_image_ids = request.POST.getlist('delete_images')
        new_images = request.FILES.getlist('new_images')
        valores = {
            'nombre': nombre,
            'tipo': tipo,
            'tipo_otro': tipo_otro,
            'unidad': unidad,
            'precio': precio,
            'stock': stock,
            'descripcion': descripcion,
            'garantia': garantia,
        }
        # Validaciones básicas
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
        if not garantia:
            errores['garantia'] = 'La garantía es obligatoria.'
        # Imágenes
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
        # Validación de modelo
        if not errores:
            producto.nombre = nombre
            producto.tipo = tipo
            producto.tipo_otro = tipo_otro
            producto.unidad = unidad
            producto.precio = precio
            producto.stock = stock
            producto.descripcion = descripcion
            producto.garantia = garantia
            if int(stock) <= 0:
                producto.is_active = False
            # método de pago y entrega eliminados
            try:
                producto.full_clean()
            except ValidationError as exc:
                for field, messages in exc.message_dict.items():
                    errores[field] = messages[0] if messages else 'Valor inválido.'
            else:
                producto.save()
                if delete_qs.exists():
                    delete_qs.delete()
                for image_file in new_images:
                    ProductImage.objects.create(product=producto, image=image_file)
                success = True
                existing_images = producto.images.all().order_by('-created_at')
                can_upload_more_images = existing_images.count() < 8
    if success:
        return redirect('administrador:producs_page')
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
# Bloquear/desbloquear producto desde admin
from Productos.models import Product
from django.views.decorators.http import require_POST

@require_POST
def producto_admin_block_view(request, product_id):
    """Marca un producto como inactivo."""
    # Cambia el estado del producto a inactivo.
    producto = get_object_or_404(Product, id=product_id)
    producto.is_active = False
    producto.disabled_by_admin = True
    producto.save(update_fields=["is_active", "disabled_by_admin"])
    return JsonResponse({'ok': True})

@require_POST
def producto_admin_unblock_view(request, product_id):
    """Marca un producto como activo."""
    # Cambia el estado del producto a activo.
    producto = get_object_or_404(Product, id=product_id)
    producto.is_active = True
    producto.disabled_by_admin = False
    producto.save(update_fields=["is_active", "disabled_by_admin"])
    return JsonResponse({'ok': True})


def admin_notifications_view(request):
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    from usuarios.models import Register
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return redirect('usuarios:home_customer')

    from Mensajes.models import AdminNotification

    notifications = AdminNotification.objects.select_related(
        'sender_register',
        'sender_user',
        'product',
    ).order_by('-created_at')

    return render(request, 'administrador/admin_notifications.html', {
        'notifications': notifications,
    })


@require_POST
def admin_notification_mark_read_view(request, notification_id):
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    from usuarios.models import Register
    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return redirect('usuarios:home_customer')

    from Mensajes.models import AdminNotification

    notification = get_object_or_404(AdminNotification, id=notification_id)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])

    return redirect('administrador:admin_notifications')
# ============================================================
# BLOQUE 4: MENSAJERIA ADMINISTRATIVA
# ============================================================

# Enviar mensaje general (a todos, solo usuarios o solo tiendas)
@require_POST
def usuario_admin_enviar_mensaje_general_view(request):
    """Envía un mensaje masivo a usuarios, tiendas o ambos segmentos.

    El mensaje se registra en AdminToUserMessage y también se intenta enviar por email.
    """
    # Envía mensaje masivo segmentado y registra trazabilidad en base de datos.
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'No autenticado'}, status=403)

    from usuarios.models import Register

    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    import json
    from Mensajes.models import AdminToUserMessage
    from Tiendas.models import Shop
    from django.core.mail import send_mail

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    texto = (data.get('mensaje') or '').strip()
    destinatario = data.get('destinatario', 'all')

    if not texto:
        return JsonResponse({'ok': False, 'error': 'Mensaje vacío'}, status=400)

    usuarios = []
    if destinatario == 'all':
        usuarios = list(Register.objects.all())
    elif destinatario == 'users':
        # Excluir usuarios que son dueños de tienda
        usuarios_con_tienda = Shop.objects.values_list('owner__id', flat=True)
        usuarios = list(Register.objects.exclude(id_usuario__in=usuarios_con_tienda))
    elif destinatario == 'shops':
        # Solo dueños de tienda
        usuarios_con_tienda = Shop.objects.values_list('owner__id', flat=True)
        usuarios = list(Register.objects.filter(id_usuario__in=usuarios_con_tienda))
    else:
        return JsonResponse({'ok': False, 'error': 'Destinatario inválido'}, status=400)

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

    return JsonResponse({'ok': True, 'enviados': len(usuarios)})
# ============================================================
# BLOQUE 5: PERFIL ADMIN Y FORMULARIO DE USUARIO ADMIN
# ============================================================

# Vista para editar el perfil del admin autenticado
from django.contrib.auth.decorators import login_required
def admin_editar_perfil_view(request):
    """Permite al admin editar su perfil y datos de tienda relacionados."""
    # Permite al admin actualizar sus datos y, si aplica, datos de su tienda.
    from usuarios.models import Register
    admin_id = request.session.get('admin_user_id')
    if not admin_id:
        return redirect('usuarios:login')
    usuario = get_object_or_404(Register, id_usuario=admin_id)
    tienda = Shop.objects.filter(owner__id=usuario.id_usuario).first()
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
        form = UsuarioAdminForm(instance=usuario)
    return render(request, 'administrador/usuario_editar_admin.html', {'form': form, 'usuario': usuario, 'tienda': tienda, 'es_perfil_admin': True})
from django.shortcuts import render, get_object_or_404, redirect
from django import forms
from django.http import JsonResponse, HttpResponse
import csv
from reportlab.lib import colors  # pyright: ignore[reportMissingImports]
from reportlab.lib.pagesizes import A4, landscape  # pyright: ignore[reportMissingImports]
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # pyright: ignore[reportMissingImports]
from reportlab.lib.units import cm  # pyright: ignore[reportMissingImports]
from reportlab.lib.enums import TA_CENTER  # pyright: ignore[reportMissingImports]
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer  # pyright: ignore[reportMissingImports]
from xml.sax.saxutils import escape
from usuarios.models import Register
from Tiendas.models import Shop
from django.contrib.auth.models import User

class UsuarioAdminForm(forms.ModelForm):
    """Formulario de edición de perfil de usuario en administración."""
    # Formulario técnico para edición de usuarios desde el panel admin.
    class Meta:
        from usuarios.models import Register
        model = Register
        fields = [
            'foto', 'tipo_documento', 'numero_documento', 'nombres', 'apellidos',
            'correo_electronico', 'telefono', 'departamento', 'municipio',
            'direccion_completa', 'descripcion_perfil', 'estado'
        ]
        widgets = {
            'estado': forms.Select(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')]),
            'descripcion_perfil': forms.Textarea(attrs={'rows': 2}),
        }

def usuario_admin_editar_view(request, usuario_id):
    """Edita un usuario y, si aplica, su tienda asociada."""
    # Edición integral de usuario y sincronización de tienda asociada.
    from usuarios.models import Register
    usuario = get_object_or_404(Register, id=usuario_id)
    tienda = Shop.objects.filter(owner__id=usuario.id_usuario).first()
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            # Guardar datos de tienda si existen
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
            return redirect('administrador:usuario_admin_detalle', usuario_id=usuario.id)
    else:
        form = UsuarioAdminForm(instance=usuario)
    return render(request, 'administrador/usuario_editar_admin.html', {'form': form, 'usuario': usuario, 'tienda': tienda})


@require_POST
def usuario_admin_enviar_recuperacion_view(request, usuario_id):
    """Envía al usuario un código de recuperación de contraseña desde el panel admin."""
    from usuarios.models import Register
    from django.urls import reverse
    from django.utils import timezone
    from datetime import timedelta
    from django.core.mail import send_mail
    from django.conf import settings
    import random
    import string

    usuario = get_object_or_404(Register, id=usuario_id)
    redirect_url = reverse('administrador:usuario_admin_editar', args=[usuario.id])

    if not usuario.correo_electronico:
        return redirect(f"{redirect_url}?recovery_mail=missing_email")

    codigo = ''.join(random.choices(string.digits, k=6))
    usuario.codigo_reset = codigo
    usuario.fecha_expiracion_codigo = timezone.now() + timedelta(minutes=15)
    usuario.save(update_fields=['codigo_reset', 'fecha_expiracion_codigo'])

    try:
        send_mail(
            subject='Código para restablecer contraseña - Agrophia',
            message=(
                f'Hola {usuario.nombres},\n\n'
                f'Tu código para restablecer la contraseña es: {codigo}\n\n'
                'Este código es válido por 15 minutos.\n\n'
                'Si no solicitaste restablecer tu contraseña, ignora este mensaje.\n\n'
                'Saludos,\nEquipo Agrophia'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.correo_electronico],
            fail_silently=False,
        )
    except Exception:
        return redirect(f"{redirect_url}?recovery_mail=error")

    return redirect(f"{redirect_url}?recovery_mail=sent")
# Vista para detalle de usuario admin
from django.shortcuts import get_object_or_404

def usuario_admin_detalle_view(request, usuario_id):
    """Renderiza detalle de usuario para consulta administrativa."""
    # Vista de solo lectura para perfil de usuario y su tienda vinculada.
    from usuarios.models import Register
    usuario = get_object_or_404(Register, id=usuario_id)
    tienda = Shop.objects.filter(owner__id=usuario.id_usuario).first()
    return render(request, 'administrador/usuario_detalle_admin.html', {'usuario': usuario, 'tienda': tienda})
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime
import csv

def admin_verify_code_view(request):
    pending_user_id = request.session.get('pending_admin_user_id')
    pending_register_id = request.session.get('pending_admin_register_id')
    pending_code = request.session.get('pending_admin_code')
    expires_iso = request.session.get('pending_admin_code_expires_at')

    if not pending_user_id or not pending_register_id or not pending_code or not expires_iso:
        messages.error(request, 'Primero debes iniciar sesion como administrador para generar tu codigo de seguridad.')
        return redirect('usuarios:login')

    try:
        expires_at = datetime.fromisoformat(expires_iso)
    except (TypeError, ValueError):
        request.session.pop('pending_admin_user_id', None)
        request.session.pop('pending_admin_register_id', None)
        request.session.pop('pending_admin_code', None)
        request.session.pop('pending_admin_code_expires_at', None)
        messages.error(request, 'El codigo no es valido. Inicia sesion nuevamente.')
        return redirect('usuarios:login')

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

    if request.method == 'POST':
        code_input = (request.POST.get('code') or '').strip().upper()
        if len(code_input) != 6:
            messages.error(request, 'El codigo debe tener 6 caracteres.')
            return render(request, 'administrador/admin_verify_code.html', {
                'remaining_seconds': int((expires_at - timezone.now()).total_seconds()),
            })

        if code_input != pending_code:
            messages.error(request, 'Codigo incorrecto.')
            return render(request, 'administrador/admin_verify_code.html', {
                'remaining_seconds': int((expires_at - timezone.now()).total_seconds()),
            })

        user = User.objects.filter(id=pending_user_id).first()
        reg = Register.objects.filter(id=pending_register_id, estado='admin').first()
        if not user or not reg:
            request.session.pop('pending_admin_user_id', None)
            request.session.pop('pending_admin_register_id', None)
            request.session.pop('pending_admin_code', None)
            request.session.pop('pending_admin_code_expires_at', None)
            messages.error(request, 'No se pudo validar el administrador.')
            return redirect('usuarios:login')

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

    return render(request, 'administrador/admin_verify_code.html', {
        'remaining_seconds': max(0, int((expires_at - timezone.now()).total_seconds())),
    })


def admin_logout_view(request):
    """Cierra sesión admin y limpia banderas de validación del código admin."""
    # Logout limpio + limpieza de bandera de validación de código admin.
    # Al cerrar sesión, limpiar validación en la base de datos
    user_id = request.session.get('admin_user_id')
    if user_id:
        try:
            reg = Register.objects.get(id_usuario=user_id)
            reg.admin_code_validated = False
            reg.save()
        except Register.DoesNotExist:
            pass
    logout(request)
    request.session.flush()
    return redirect('/')

# ============================================================
# BLOQUE 7: UTILIDADES DE ACTIVIDAD Y ORDENAMIENTO
# ============================================================

def safe_fecha(fecha):
    """Devuelve una fecha formateada de manera segura para UI/reportes."""
    # Formatea fecha de forma segura para UI/reportes.
    if hasattr(fecha, 'strftime'):
        try:
            fecha_local = timezone.localtime(fecha)
        except Exception:
            fecha_local = fecha
        return fecha_local.strftime('%d/%m/%Y %H:%M')
    return 'Sin fecha'

def activity_category_label(category):
    """Mapea la categoría interna de actividad a una etiqueta visible."""
    # Convierte clave técnica de categoría a etiqueta legible.
    labels = {
        'all': 'Toda la actividad',
        'users': 'Usuarios',
        'shops': 'Tiendas',
        'products': 'Productos',
        'orders': 'Pedidos',
    }
    return labels.get(category, 'Actividad')

def _activity_timestamp(fecha):
    """Convierte una fecha a timestamp numérico para ordenamiento estable."""
    # Obtiene timestamp numérico para llaves de ordenamiento robustas.
    if hasattr(fecha, 'timestamp'):
        return fecha.timestamp()
    return 0

def activity_latest_sort_key(evento):
    """Clave de ordenamiento para eventos del más reciente al más antiguo."""
    # Orden descendente por fecha (más reciente primero).
    fecha = evento.get('occurred_at')
    return (0 if fecha else 1, -_activity_timestamp(fecha), evento.get('sequence', 0))

def activity_first_sort_key(evento):
    """Clave de ordenamiento para eventos del más antiguo al más reciente."""
    # Orden ascendente por fecha (más antiguo primero).
    fecha = evento.get('occurred_at')
    return (0 if fecha else 1, _activity_timestamp(fecha), evento.get('sequence', 0))

def build_activity_events():
    """Construye una colección unificada de eventos del sistema.

    Fuentes incluidas:
    - Register (altas y bloqueos).
    - Shop (creación y deshabilitación).
    - Product (creación y deshabilitación).
    - Order (nuevos pedidos).
    """
    # Construye una línea de tiempo unificada desde usuarios, tiendas, productos y pedidos.
    eventos = []
    sequence = 0

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
    """Filtra eventos según criterios de reporte.

    Args:
        events: Lista de eventos preconstruidos.
        category: Categoria deseada (all/users/shops/products/orders).
        scope: Alcance (all/count/period).
        count_mode: latest o first.
        count_value: Cantidad a retornar cuando scope=count.
        period: month o year para scope=period.
    """
    # Filtra y recorta eventos según categoría, alcance temporal y modo de conteo.
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

    filtrados = [
        evento for evento in events
        if category == 'all' or evento['category'] == category
    ]

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

    if scope == 'count':
        try:
            count = int(count_value)
        except (TypeError, ValueError):
            count = 100
        count = max(1, min(count, 1000))
        sort_key = activity_latest_sort_key if count_mode == 'latest' else activity_first_sort_key
        return sorted(filtrados, key=sort_key)[:count]

    return sorted(filtrados, key=activity_latest_sort_key)

def activity_scope_label(scope, count_mode='latest', count_value=100, period='month'):
    """Genera el subtítulo legible del alcance aplicado al reporte."""
    # Etiqueta human-readable del alcance aplicado al reporte de actividad.
    if scope == 'count':
        prefix = 'Ultimas' if count_mode == 'latest' else 'Primeras'
        return f"{prefix} {count_value} actividades"
    if scope == 'period':
        return 'Actividades de este mes' if period == 'month' else 'Actividades de este año'
    return 'Toda la actividad disponible'


def resolve_selected_fields(request, allowed_fields, default_fields=None):
    """Valida y resuelve campos seleccionados en reportes dinámicos."""
    allowed_keys = set(allowed_fields.keys())

    selected = []
    for raw in request.GET.getlist('fields'):
        for chunk in str(raw).split(','):
            key = chunk.strip()
            if key:
                selected.append(key)

    all_requested = str(request.GET.get('all_fields', '')).lower() in {'1', 'true', 'on', 'si'}
    if all_requested or not selected:
        selected = list(default_fields or allowed_fields.keys())

    clean_selected = []
    seen = set()
    for key in selected:
        if key in allowed_keys and key not in seen:
            clean_selected.append(key)
            seen.add(key)

    if not clean_selected:
        clean_selected = list(default_fields or allowed_fields.keys())

    return clean_selected


def build_individual_user_history(usuario):
    """Construye historial de actividad para un usuario específico."""
    from Pedidos.models import Order, OrderItem
    from Tiendas.models import Shop
    from Productos.models import Product
    from django.contrib.auth.models import User

    history = []
    auth_user_id = usuario.id_usuario
    auth_user = User.objects.filter(id=auth_user_id).first() if auth_user_id else None

    shops = list(Shop.objects.filter(owner_id=auth_user_id).order_by('-created_at'))
    account_type = 'Tienda' if shops else 'Cliente'

    def add_history(occurred_at, area, action, detail):
        history.append({
            'occurred_at': occurred_at,
            'area': area,
            'accion': action,
            'detalle': detail,
        })

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

    if account_type == 'Cliente' and not customer_orders.exists():
        add_history(None, 'Compras', 'Sin compras registradas', 'No se encontraron pedidos realizados por este usuario')
    if account_type == 'Tienda' and not sale_items.exists():
        add_history(None, 'Ventas', 'Sin ventas registradas', 'No se encontraron ventas asociadas a esta cuenta de tienda')

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

    history = []

    def add_history(occurred_at, area, action, detail):
        history.append({
            'occurred_at': occurred_at,
            'area': area,
            'accion': action,
            'detalle': detail,
        })

    add_history(
        tienda.created_at,
        'Tienda',
        'Tienda creada',
        f"Tienda registrada: {tienda.nombre} ({tienda.municipio}, {tienda.departamento})",
    )

    if not tienda.is_active:
        add_history(None, 'Tienda', 'Tienda deshabilitada', f"Tienda deshabilitada: {tienda.nombre}")

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

    if not products.exists():
        add_history(None, 'Productos', 'Sin productos registrados', 'No se encontraron productos asociados a esta tienda')
    if not sale_items.exists():
        add_history(None, 'Ventas', 'Sin ventas registradas', 'No se encontraron ventas asociadas a esta tienda')

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

    def _cell_to_paragraph(value):
        text = '' if value is None else str(value)
        return Paragraph(escape(text).replace('\n', '<br/>'), cell_style)

    def _header_to_paragraph(value):
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

    elements = [header_box]

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
# ============================================================

def home_admin_view(request):
    """Renderiza el home admin con los últimos eventos de actividad."""
    # Home administrativa mostrando resumen de actividad reciente.
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
    if not register_admin:
        logout(request)
        request.session.flush()
        return redirect('usuarios:login')

    if request.session.get('admin_user_id') != request.user.id or not register_admin.admin_code_validated:
        messages.error(request, 'Debes completar la verificacion de seguridad para ingresar al panel.')
        return redirect('administrador:admin_verify_code')

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
    return render(request, 'administrador/home_admin.html', {'eventos': eventos})

def reporte_actividad_reciente_view(request):
    """Genera reporte de actividad reciente en PDF.

    Admite filtros por categoría, alcance, periodo y modo de conteo.
    """
    # Genera reporte de actividad reciente en PDF.
    activity_type = request.GET.get('activity_type', 'all')
    scope = request.GET.get('scope', 'all')
    count_mode = request.GET.get('count_mode', 'latest')
    count_value = request.GET.get('count_value', '100')
    period = request.GET.get('period', 'month')

    eventos = filter_activity_events(
        build_activity_events(),
        category=activity_type,
        scope=scope,
        count_mode=count_mode,
        count_value=count_value,
        period=period,
    )

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
# ============================================================

def usuarios_admin_view(request):
    """Renderiza listado de usuarios administrables (excluye admins)."""
    # Lista general de usuarios no administradores.
    from Administrador.departamentos_municipios import DEPARTAMENTOS_MUNICIPIOS
    usuarios = Register.objects.exclude(estado='admin').order_by('nombres', 'apellidos')
    return render(request, 'administrador/usuarios_admin.html', {
        'usuarios': usuarios,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
    })

def orders_page_view(request):
    """Renderiza vista administrativa de pedidos."""
    # Vista tabla de pedidos para administración.
    pedidos = Order.objects.select_related('customer').order_by('-created_at')
    return render(request, 'administrador/orders_page.html', {'pedidos': pedidos})

def producs_page_view(request):
    """Renderiza vista administrativa de productos."""
    # Vista tabla de productos para administración.
    productos = Product.objects.all().order_by('-created_at')
    return render(request, 'administrador/producs_page.html', {'productos': productos})

def usuario_admin_block_view(request, usuario_id):
    """Bloquea un usuario (estado=inactivo) vía endpoint POST."""
    # Bloquea usuario cambiando estado a inactivo.
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    usuario = get_object_or_404(Register, id=usuario_id)
    usuario.estado = 'inactivo'
    usuario.save(update_fields=['estado'])
    return JsonResponse({'ok': True})

def usuario_admin_unblock_view(request, usuario_id):
    """Desbloquea un usuario (estado=activo) vía endpoint POST."""
    # Desbloquea usuario cambiando estado a activo.
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    usuario = get_object_or_404(Register, id=usuario_id)
    usuario.estado = 'activo'
    usuario.save(update_fields=['estado'])
    return JsonResponse({'ok': True})

def usuario_admin_enviar_mensaje_view(request, usuario_id):
    """Envía mensaje administrativo individual a un usuario."""
    # Envío individual de mensaje administrativo a un usuario.
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    import json
    from Mensajes.models import AdminToUserMessage
    from django.core.mail import send_mail

    usuario = get_object_or_404(Register, id=usuario_id)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}

    texto = (data.get('mensaje') or '').strip()
    if not texto:
        return JsonResponse({'ok': False, 'error': 'Mensaje vacío'}, status=400)

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
    return JsonResponse({'ok': True})

def reporte_usuarios_view(request):
    """Genera reporte de usuarios en formato PDF."""
    # Exporta listado de usuarios en PDF.
    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    usuario_id = (request.GET.get('usuario_id') or '').strip()

    if scope not in {'general', 'individual'}:
        scope = 'general'

    if scope == 'individual' and not usuario_id:
        scope = 'general'

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
        # Respeta la seleccion de campos enviada desde el toolbar tambien
        # para el reporte individual (no forzar todos los campos).
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

    return render_generic_report_pdf('Reporte de usuarios', headers, rows, subtitle=subtitle)

def usuario_admin_crear_view(request):
    """Crea un usuario desde admin con validaciones de datos y duplicados."""
    # Registro manual de usuario desde panel administrativo.
    from usuarios.models import Register
    from django.contrib.auth.models import User
    from django.contrib.auth.hashers import make_password
    success = False
    errores = {}
    valores = {}
    if request.method == 'POST':
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
        # Validaciones
        if not nombres:
            errores['nombres'] = 'El nombre es obligatorio.'
        if not apellidos:
            errores['apellidos'] = 'El apellido es obligatorio.'
        if not tipo_documento:
            errores['tipo_documento'] = 'El tipo de documento es obligatorio.'
        if not numero_documento:
            errores['numero_documento'] = 'El número de documento es obligatorio.'
        elif Register.objects.filter(numero_documento=numero_documento).exists():
            errores['numero_documento'] = 'Ya existe un usuario con ese número de documento.'
        if not correo_electronico:
            errores['correo_electronico'] = 'El correo es obligatorio.'
        elif Register.objects.filter(correo_electronico=correo_electronico).exists():
            errores['correo_electronico'] = 'Ya existe un usuario con ese correo.'
        if not telefono:
            errores['telefono'] = 'El teléfono es obligatorio.'
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
        if not contrasena or len(contrasena) < 8:
            errores['contrasena'] = 'La contraseña es obligatoria y debe tener al menos 8 caracteres.'
        if not errores:
            user, created = User.objects.get_or_create(
                username=numero_documento,
                defaults={
                    'email': correo_electronico,
                    'first_name': nombres,
                    'last_name': apellidos
                }
            )
            user.email = correo_electronico
            user.first_name = nombres
            user.last_name = apellidos
            user.set_password(contrasena)
            user.save(update_fields=['email', 'first_name', 'last_name', 'password'])

            Register.objects.create(
                id_usuario=user.id,
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
# ============================================================

def pedido_admin_detalle_view(request, pedido_id):
    """Muestra detalle de un pedido y sus ítems asociados."""
    # Detalle de pedido y sus ítems con producto/agricultor relacionados.
    pedido = get_object_or_404(Order, id=pedido_id)
    items = pedido.items.select_related('product', 'farmer').all()
    return render(request, 'administrador/pedido_detalle_card.html', {
        'pedido': pedido,
        'items': items,
    })

def pedido_admin_editar_view(request, pedido_id):
    """Permite editar estado y dirección de entrega de un pedido."""
    # Edición administrativa del estado y dirección de entrega del pedido.
    pedido = get_object_or_404(Order, id=pedido_id)
    errores = {}
    if request.method == 'POST':
        status = request.POST.get('status', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        # Validaciones básicas
        if status not in dict(Order.STATUS_CHOICES):
            errores['status'] = 'Estado inválido.'
        if not delivery_address:
            errores['delivery_address'] = 'La dirección de entrega es obligatoria.'
        if not errores:
            pedido.status = status
            pedido.delivery_address = delivery_address
            pedido.save()
            return redirect('administrador:orders_page')
    items = pedido.items.select_related('product', 'farmer').all()
    return render(request, 'administrador/pedido_editar_card.html', {
        'pedido': pedido,
        'items': items,
        'errores': errores,
        'status_choices': Order.STATUS_CHOICES,
    })

def reporte_pedidos_view(request):
    """Genera reporte de pedidos filtrable por estado (PDF)."""
    # Reporte de pedidos filtrable por estado (PDF).
    # Normaliza etiquetas de metodo de pago para salida consistente en PDF.
    def format_payment_method(raw_value):
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

    # Normaliza etiquetas de metodo de entrega para salida consistente en PDF.
    def format_delivery_method(raw_value):
        value = (raw_value or '').strip().lower()
        if not value:
            return 'No registrado'
        if 'tienda' in value or 'recog' in value or 'pickup' in value:
            return 'Recoger en tienda'
        if 'domicilio' in value or 'entrega' in value or 'delivery' in value:
            return 'Domicilio'
        return (raw_value or '').strip()

    # Si el pedido es para recoger en tienda, no expone direccion de domicilio.
    def format_delivery_address(order_obj):
        method = format_delivery_method(order_obj.delivery_method)
        if method == 'Recoger en tienda':
            return 'Recoger en tienda'
        return order_obj.delivery_address or ''

    scope = (request.GET.get('report_scope') or 'general').strip().lower()
    pedido_id = (request.GET.get('pedido_id') or '').strip()

    if scope not in {'general', 'individual'}:
        scope = 'general'

    if scope == 'individual' and not pedido_id:
        scope = 'general'

    if scope == 'individual':
        # Reporte puntual: perfil del pedido + tabla secundaria de items.
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

    estado = request.GET.get('estado', 'todos')
    # Reporte general: solo filtra por estado (se retira filtro por cliente).
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

    subtitle = 'Estado: Todos' if estado == 'todos' else f'Estado: {estado}'
    return render_generic_report_pdf('Reporte de pedidos', headers, rows, subtitle=subtitle)
