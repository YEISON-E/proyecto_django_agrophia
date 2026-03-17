# --- Gestión de tiendas admin ---
from Tiendas.models import Shop
from django.views.decorators.http import require_POST

def store_admin_view(request):
    tiendas = Shop.objects.all().order_by('-created_at')
    return render(request, 'administrador/store_admin.html', {'tiendas': tiendas})

def tienda_admin_detalle_view(request, tienda_id):
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
    tienda = get_object_or_404(Shop, id=tienda_id)
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
        valores = {
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
            tienda.nombre = nombre
            tienda.telefono = telefono
            tienda.email = email
            tienda.departamento = departamento
            tienda.municipio = municipio
            tienda.direccion = direccion
            tienda.horario = horario
            tienda.descripcion = descripcion
            tienda.save()
            success = True
        return render(request, 'administrador/tienda_editar_admin.html', {
            'success': success,
            'errores': errores,
            'valores': valores,
            'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
            'tienda': tienda,
        })
    return render(request, 'administrador/tienda_editar_admin.html', {
        'success': success,
        'errores': errores,
        'valores': valores,
        'departamentos_municipios': DEPARTAMENTOS_MUNICIPIOS,
        'tienda': tienda,
    })

@require_POST
def tienda_admin_block_view(request, tienda_id):
    tienda = get_object_or_404(Shop, id=tienda_id)
    tienda.is_active = False
    tienda.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})

@require_POST
def tienda_admin_unblock_view(request, tienda_id):
    tienda = get_object_or_404(Shop, id=tienda_id)
    tienda.is_active = True
    tienda.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})

# Reporte de tiendas
def reporte_tiendas_view(request):
    output_format = request.GET.get('output_format', 'excel')
    tiendas = Shop.objects.all().order_by('-created_at')
    headers = ['ID', 'Nombre', 'Teléfono', 'Correo', 'Departamento', 'Municipio', 'Dirección', 'Horario', 'Estado', 'Fecha creación']
    rows = [
        [
            t.id,
            t.nombre,
            t.telefono,
            t.email,
            t.departamento,
            t.municipio,
            t.direccion,
            t.horario,
            'Activo' if t.is_active else 'Inactivo',
            t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else ''
        ]
        for t in tiendas
    ]

    if output_format == 'print':
        return render_generic_report_print(request, 'Reporte de tiendas', headers, rows)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Tiendas Agrophia'
    ws.append(headers)
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='16A34A', end_color='16A34A', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    for row in rows:
        ws.append(row)
    autofit_worksheet_columns(ws)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="tiendas_agrophia.xlsx"'
    wb.save(response)
    return response
# Reporte de productos
def reporte_productos_view(request):
    from Productos.models import Product
    output_format = request.GET.get('output_format', 'excel')
    productos = Product.objects.all().order_by('-created_at')
    headers = ['ID', 'Nombre', 'Tipo', 'Unidad', 'Precio', 'Descripción', 'Garantía', 'Estado', 'Fecha creación']
    rows = [
        [
            p.id,
            p.nombre,
            f"{p.tipo} ({p.tipo_otro})" if p.tipo == 'Otros' and p.tipo_otro else p.tipo,
            p.unidad,
            str(p.precio),
            p.descripcion,
            p.garantia,
            'Activo' if p.is_active else 'Inactivo',
            p.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(p, 'created_at') and p.created_at else ''
        ]
        for p in productos
    ]

    if output_format == 'print':
        return render_generic_report_print(request, 'Reporte de productos', headers, rows)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Productos Agrophia'
    ws.append(headers)
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='6366F1', end_color='6366F1', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    for row in rows:
        ws.append(row)
    autofit_worksheet_columns(ws)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="productos_agrophia.xlsx"'
    wb.save(response)
    return response
# Vista detalle producto admin
def producto_admin_detalle_view(request, product_id):
    from Productos.models import Product
    producto = get_object_or_404(Product, id=product_id)
    return render(request, 'administrador/producto_detalle_admin.html', {'producto': producto})
from Productos.models import Product, ProductImage
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
# --- Vistas para crear y editar productos desde el admin ---
def producto_admin_crear_view(request):
    success = False
    errores = {}
    valores = {}
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', '').strip()
        tipo_otro = request.POST.get('tipo_otro', '').strip()
        unidad = request.POST.get('unidad', '').strip()
        precio = request.POST.get('precio', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        garantia = request.POST.get('garantia', '').strip()
        fotos = request.FILES.getlist('fotos')
        valores = {
            'nombre': nombre,
            'tipo': tipo,
            'tipo_otro': tipo_otro,
            'unidad': unidad,
            'precio': precio,
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
                descripcion=descripcion,
                garantia=garantia,
                is_active=True,
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
    producto = get_object_or_404(Product, id=product_id)
    success = False
    errores = {}
    valores = {
        'nombre': producto.nombre,
        'tipo': producto.tipo,
        'tipo_otro': producto.tipo_otro,
        'unidad': producto.unidad,
        'precio': producto.precio,
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
            producto.descripcion = descripcion
            producto.garantia = garantia
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
    producto = get_object_or_404(Product, id=product_id)
    producto.is_active = False
    producto.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})

@require_POST
def producto_admin_unblock_view(request, product_id):
    producto = get_object_or_404(Product, id=product_id)
    producto.is_active = True
    producto.save(update_fields=["is_active"])
    return JsonResponse({'ok': True})
# Enviar mensaje general (a todos, solo usuarios o solo tiendas)
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def usuario_admin_enviar_mensaje_general_view(request):
    if request.method == 'POST':
        import json
        from Mensajes.models import AdminToUserMessage
        from usuarios.models import Register
        from Tiendas.models import Shop
        from django.core.mail import send_mail
        data = json.loads(request.body)
        texto = data.get('mensaje', '').strip()
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
    return JsonResponse({'ok': False}, status=400)
# Vista para editar el perfil del admin autenticado
from django.contrib.auth.decorators import login_required
def admin_editar_perfil_view(request):
    from usuarios.models import Register
    admin_id = request.session.get('admin_user_id')
    if not admin_id:
        return redirect('administrador:admin_login')
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
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from usuarios.models import Register
from Tiendas.models import Shop
from django.contrib.auth.models import User

class UsuarioAdminForm(forms.ModelForm):
	contrasena = forms.CharField(label='Contraseña', widget=forms.TextInput(attrs={'type': 'text'}), required=False)
	class Meta:
		from usuarios.models import Register
		model = Register
		fields = [
			'foto', 'tipo_documento', 'numero_documento', 'nombres', 'apellidos',
			'correo_electronico', 'telefono', 'departamento', 'municipio',
			'direccion_completa', 'descripcion_perfil', 'estado', 'contrasena'
		]
		widgets = {
			'estado': forms.Select(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')]),
			'descripcion_perfil': forms.Textarea(attrs={'rows': 2}),
		}

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.cleaned_data.get('contrasena'):
			instance.contrasena = self.cleaned_data['contrasena']
		if commit:
			instance.save()
		return instance

def usuario_admin_editar_view(request, usuario_id):
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
# Vista para detalle de usuario admin
from django.shortcuts import get_object_or_404

def usuario_admin_detalle_view(request, usuario_id):
	from usuarios.models import Register
	usuario = get_object_or_404(Register, id=usuario_id)
	tienda = Shop.objects.filter(owner__id=usuario.id_usuario).first()
	return render(request, 'administrador/usuario_detalle_admin.html', {'usuario': usuario, 'tienda': tienda})
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.http import HttpResponse
import csv

def admin_login_view(request):
	if request.method == 'POST':
		documento = request.POST.get('documento')
		password = request.POST.get('password')
		try:
			reg = Register.objects.get(numero_documento=documento)
			user = User.objects.get(id=reg.id_usuario)
		except (Register.DoesNotExist, User.DoesNotExist):
			messages.error(request, 'Credenciales incorrectas')
			return render(request, 'administrador/admin_login.html')
			user_auth = authenticate(request, username=user.username, password=password)
			if user_auth and reg.estado == 'admin':
				login(request, user_auth)
				return redirect('home_admin')
		else:
			messages.error(request, 'Credenciales incorrectas o no es administrador')
	return render(request, 'administrador/admin_login.html')


def admin_logout_view(request):
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

def safe_fecha(fecha):
    if hasattr(fecha, 'strftime'):
        return fecha.strftime('%d/%m/%Y %H:%M')
    return 'Sin fecha'

def activity_category_label(category):
    labels = {
        'all': 'Toda la actividad',
        'users': 'Usuarios',
        'shops': 'Tiendas',
        'products': 'Productos',
        'orders': 'Pedidos',
    }
    return labels.get(category, 'Actividad')

def _activity_timestamp(fecha):
    if hasattr(fecha, 'timestamp'):
        return fecha.timestamp()
    return 0

def activity_latest_sort_key(evento):
    fecha = evento.get('occurred_at')
    return (0 if fecha else 1, -_activity_timestamp(fecha), evento.get('sequence', 0))

def activity_first_sort_key(evento):
    fecha = evento.get('occurred_at')
    return (0 if fecha else 1, _activity_timestamp(fecha), evento.get('sequence', 0))

def build_activity_events():
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
    if scope == 'count':
        prefix = 'Ultimas' if count_mode == 'latest' else 'Primeras'
        return f"{prefix} {count_value} actividades"
    if scope == 'period':
        return 'Actividades de este mes' if period == 'month' else 'Actividades de este año'
    return 'Toda la actividad disponible'

def autofit_worksheet_columns(ws):
    from openpyxl.utils import get_column_letter

    for col_index, col in enumerate(ws.iter_cols(min_col=1, max_col=ws.max_column), start=1):
        max_length = 0
        for cell in col:
            try:
                cell_value = '' if cell.value is None else str(cell.value)
                if len(cell_value) > max_length:
                    max_length = len(cell_value)
            except Exception:
                pass
        ws.column_dimensions[get_column_letter(col_index)].width = min(max_length + 2, 60)

def render_generic_report_print(request, title, headers, rows, subtitle=''):
    return render(request, 'administrador/reporte_generico_print.html', {
        'title': title,
        'headers': headers,
        'rows': rows,
        'subtitle': subtitle,
    })

def home_admin_view(request):
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
    activity_type = request.GET.get('activity_type', 'all')
    scope = request.GET.get('scope', 'all')
    count_mode = request.GET.get('count_mode', 'latest')
    count_value = request.GET.get('count_value', '100')
    period = request.GET.get('period', 'month')
    output_format = request.GET.get('output_format', 'excel')

    eventos = filter_activity_events(
        build_activity_events(),
        category=activity_type,
        scope=scope,
        count_mode=count_mode,
        count_value=count_value,
        period=period,
    )

    resumen = {
        'tipo_actividad': activity_category_label(activity_type),
        'alcance': activity_scope_label(scope, count_mode, count_value, period),
        'total_resultados': len(eventos),
    }

    if output_format == 'print':
        return render(request, 'administrador/reporte_actividad_reciente_print.html', {
            'eventos': [
                {
                    'fecha': safe_fecha(evento['occurred_at']),
                    'categoria': activity_category_label(evento['category']),
                    'tipo': evento['tipo'],
                    'descripcion': evento['descripcion'],
                }
                for evento in eventos
            ],
            'resumen': resumen,
        })

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Actividad reciente'

    ws.merge_cells('A1:D1')
    ws['A1'] = 'Reporte de actividad reciente'
    ws['A1'].font = Font(bold=True, size=14, color='FFFFFF')
    ws['A1'].fill = PatternFill(start_color='16A34A', end_color='16A34A', fill_type='solid')
    ws['A1'].alignment = Alignment(horizontal='center')

    ws.append([])
    ws.append(['Tipo de actividad', resumen['tipo_actividad'], 'Alcance', resumen['alcance']])
    ws.append(['Resultados', resumen['total_resultados'], '', ''])
    ws.append([])

    headers = ['Fecha', 'Categoria', 'Tipo', 'Descripcion']
    ws.append(headers)
    header_row_index = ws.max_row
    for cell in ws[header_row_index]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='6366F1', end_color='6366F1', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')

    for evento in eventos:
        ws.append([
            safe_fecha(evento['occurred_at']),
            activity_category_label(evento['category']),
            evento['tipo'],
            evento['descripcion'],
        ])
    autofit_worksheet_columns(ws)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="actividad_reciente_agrophia.xlsx"'
    wb.save(response)
    return response

def usuarios_admin_view(request):
    usuarios = Register.objects.exclude(estado='admin').order_by('nombres', 'apellidos')
    return render(request, 'administrador/usuarios_admin.html', {'usuarios': usuarios})

def orders_page_view(request):
    pedidos = Order.objects.select_related('customer').order_by('-created_at')
    return render(request, 'administrador/orders_page.html', {'pedidos': pedidos})

def producs_page_view(request):
    productos = Product.objects.all().order_by('-created_at')
    return render(request, 'administrador/producs_page.html', {'productos': productos})

def usuario_admin_block_view(request, usuario_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    usuario = get_object_or_404(Register, id=usuario_id)
    usuario.estado = 'inactivo'
    usuario.save(update_fields=['estado'])
    return JsonResponse({'ok': True})

def usuario_admin_unblock_view(request, usuario_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=400)

    usuario = get_object_or_404(Register, id=usuario_id)
    usuario.estado = 'activo'
    usuario.save(update_fields=['estado'])
    return JsonResponse({'ok': True})

def usuario_admin_enviar_mensaje_view(request, usuario_id):
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
    output_format = request.GET.get('output_format', 'excel')
    usuarios = Register.objects.exclude(estado='admin').order_by('nombres', 'apellidos')
    headers = ['ID', 'Nombres', 'Apellidos', 'Correo', 'Teléfono', 'Departamento', 'Municipio', 'Estado']
    rows = [
        [u.id, u.nombres, u.apellidos, u.correo_electronico, u.telefono, u.departamento, u.municipio, u.estado]
        for u in usuarios
    ]

    if output_format == 'print':
        return render_generic_report_print(request, 'Reporte de usuarios', headers, rows)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Usuarios Agrophia'
    ws.append(headers)
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='16A34A', end_color='16A34A', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    for row in rows:
        ws.append(row)
    autofit_worksheet_columns(ws)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="usuarios_agrophia.xlsx"'
    wb.save(response)
    return response

def usuario_admin_crear_view(request):
    from usuarios.models import Register
    from django.contrib.auth.models import User
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
                contrasena=contrasena,
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

def pedido_admin_detalle_view(request, pedido_id):
    pedido = get_object_or_404(Order, id=pedido_id)
    items = pedido.items.select_related('product', 'farmer').all()
    return render(request, 'administrador/pedido_detalle_card.html', {
        'pedido': pedido,
        'items': items,
    })

def pedido_admin_editar_view(request, pedido_id):
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

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.http import HttpResponse

def reporte_pedidos_view(request):
    estado = request.GET.get('estado', 'todos')
    output_format = request.GET.get('output_format', 'excel')
    queryset = Order.objects.select_related('customer').all()
    if estado and estado != 'todos':
        queryset = queryset.filter(status=estado)
    headers = ['ID', 'Cliente', 'Fecha', 'Total', 'Estado', 'Dirección de entrega']
    rows = [
        [
            p.id,
            p.customer.get_full_name() if hasattr(p.customer, 'get_full_name') else p.customer.username,
            p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else '',
            str(p.total_amount),
            p.get_status_display(),
            p.delivery_address or '',
        ]
        for p in queryset.order_by('-created_at')
    ]

    if output_format == 'print':
        subtitle = 'Estado: Todos' if estado == 'todos' else f'Estado: {estado}'
        return render_generic_report_print(request, 'Reporte de pedidos', headers, rows, subtitle=subtitle)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pedidos Agrophia'
    ws.append(headers)
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='16A34A', end_color='16A34A', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    for row in rows:
        ws.append(row)
    autofit_worksheet_columns(ws)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="pedidos_agrophia.xlsx"'
    wb.save(response)
    return response
