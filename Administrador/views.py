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

def home_admin_view(request):
	return render(request, 'administrador/home_admin.html')

def usuarios_admin_view(request):
    from usuarios.models import Register
    from Tiendas.models import Shop
    # Excluir usuarios que son dueños de tienda
    usuarios_con_tienda = Shop.objects.values_list('owner__id', flat=True)
    usuarios = Register.objects.exclude(id_usuario__in=usuarios_con_tienda)
    return render(request, 'administrador/usuarios_admin.html', {'usuarios': usuarios})

def orders_page_view(request):
	return render(request, 'administrador/orders_page.html')

def store_admin_view(request):
    from Tiendas.models import Shop
    tiendas = Shop.objects.select_related('owner').all()
    return render(request, 'administrador/store_admin.html', {'tiendas': tiendas})

def producs_page_view(request):
	return render(request, 'administrador/producs_page.html')

# Bloquear/desbloquear usuario
def usuario_admin_block_view(request, usuario_id):
    if request.method == 'POST':
        from usuarios.models import Register
        usuario = get_object_or_404(Register, id=usuario_id)
        usuario.estado = 'inactivo'
        usuario.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)

def usuario_admin_unblock_view(request, usuario_id):
    if request.method == 'POST':
        from usuarios.models import Register
        usuario = get_object_or_404(Register, id=usuario_id)
        usuario.estado = 'activo'
        usuario.save()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)

# Enviar mensaje desde admin (POST, AJAX)
def usuario_admin_enviar_mensaje_view(request, usuario_id):
    if request.method == 'POST':
        import json
        from Mensajes.models import AdminToUserMessage
        from usuarios.models import Register
        from django.core.mail import send_mail
        data = json.loads(request.body)
        texto = data.get('mensaje', '').strip()
        if texto:
            usuario = get_object_or_404(Register, id=usuario_id)
            # Guardar mensaje importante
            mensaje = AdminToUserMessage.objects.create(
                usuario=usuario,
                texto=texto,
                enviado=True
            )
            # Enviar correo
            send_mail(
                'Mensaje importante de Agrophia',
                texto,
                'no-reply@agrophia.com',
                [usuario.correo_electronico],
                fail_silently=True
            )
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'Mensaje vacío'}, status=400)
    return JsonResponse({'ok': False}, status=400)

# Reporte de usuarios
def reporte_usuarios_view(request):
    from usuarios.models import Register
    from Tiendas.models import Shop
    # Excluir usuarios con tienda y con estado 'admin'
    usuarios_con_tienda = Shop.objects.values_list('owner__id', flat=True)
    usuarios = Register.objects.exclude(id_usuario__in=usuarios_con_tienda).exclude(estado='admin')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Usuarios Agrophia'

    # Encabezados
    headers = ['ID', 'Nombres', 'Apellidos', 'Correo', 'Teléfono', 'Departamento', 'Municipio', 'Estado']
    ws.append(headers)
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='16A34A', end_color='16A34A', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    # Filas de datos
    for u in usuarios:
        ws.append([
            u.id, u.nombres, u.apellidos, u.correo_electronico, u.telefono, u.departamento, u.municipio, u.estado
        ])

    # Ajustar ancho de columnas
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[col_letter].width = max_length + 2

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
