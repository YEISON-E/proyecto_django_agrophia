"""
Vistas del modulo de tiendas.

Este modulo gestiona el flujo del agricultor y su tienda:
- Verificacion de existencia de tienda activa/inactiva.
- Creacion de tienda en dos pasos con persistencia temporal en sesion.
- Perfil de tienda y perfil publico del vendedor.
- Activacion/desactivacion de tienda y sincronizacion con productos.
- Redirecciones de rutas legacy del frontend estatico.

Aspectos importantes:
- El flujo de creacion usa token firmado para asociar propietario.
- Al desactivar tienda, tambien se desactivan sus productos.
- Las vistas del panel agricultor exigen autenticacion y tienda activa.
"""

from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
# Importación de dependencias necesarias para ejecutar esta vista.
from django.contrib.auth.models import User
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from django.urls import reverse
# Importación de dependencias necesarias para ejecutar esta vista.
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
# Importación de dependencias necesarias para ejecutar esta vista.
from datetime import datetime
from urllib.parse import urlencode
import uuid
import re

from .models import Shop
from Productos.models import Product
from usuarios.models import Register


def user_has_shop(user):
	"""Retorna `True` si el usuario autenticado tiene una tienda activa."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not user or not user.is_authenticated:
		return False
	return Shop.objects.filter(owner=user, is_active=True).exists()


def user_has_inactive_shop(user):
	"""Retorna `True` si el usuario autenticado tiene tienda inactiva."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not user or not user.is_authenticated:
		return False
	return Shop.objects.filter(owner=user, is_active=False).exists()


def resolve_legacy_tienda_route(page):
	"""Mapea rutas legacy del frontend a nombres de rutas Django."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	legacy_routes = {
		"create-shop.html": ("redirect", "tiendas:create_farmer_perfil"),
		"create-farmer-perfil.html": ("redirect", "tiendas:create_farmer_perfil"),
		"create-shop2.html": ("redirect", "tiendas:create_shop_step2"),
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"interface_farmer.html": ("redirect", "tiendas:interface_farmer"),
		"profile_shop.html": ("redirect", "tiendas:profile_shop"),
		"p_update_shop.html": ("redirect", "tiendas:update_shop_step1"),
		"p_update_shop2.html": ("redirect", "tiendas:update_shop_step2"),
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"form_subir_producto.html": ("redirect", "productos:create_product"),
		"form_subir_producto2.html": ("redirect", "productos:create_product2"),
	}
	return legacy_routes.get(page)


def _get_register_user(request):
	"""Obtiene el perfil `Register` del usuario autenticado actual."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	register_user = Register.objects.filter(id_usuario=request.user.id).first()
	if not register_user:
		register_user = Register.objects.filter(numero_documento=request.user.username).first()
	return register_user


def _get_shop_flow_owner(request):
	"""Resuelve el propietario del flujo de creacion de tienda.

	Prioriza el usuario autenticado y, si no existe, usa el ID guardado
	en sesion durante el flujo multi-paso.
	"""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if request.user.is_authenticated:
		request.session["shop_flow_owner_id"] = request.user.id
		return request.user

	owner_id = request.session.get("shop_flow_owner_id")
	if not owner_id:
		return None

	return User.objects.filter(id=owner_id).first()


def _resolve_owner_from_token(owner_token):
	"""Resuelve el usuario propietario a partir de un token firmado."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not owner_token:
		return None
	try:
		owner_data = signing.loads(owner_token, max_age=7200)
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		owner_user_id = owner_data.get("owner_user_id")
		if owner_user_id:
			return User.objects.filter(id=owner_user_id).first()
	except (BadSignature, SignatureExpired, TypeError, ValueError):
		# Retorno de respuesta según el estado y resultado de la operación.
		return None
	return None


@never_cache
def create_farmer_perfil(request):
	"""Inicia el flujo de creacion de tienda para agricultor autenticado."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")
	request.session["shop_flow_owner_id"] = request.user.id
	flow_id = uuid.uuid4().hex
	# Paso de apoyo dentro del flujo principal de la funcionalidad.
	request.session["shop_flow_id"] = flow_id
	request.session.pop("shop_step1", None)
	request.session.pop("shop_step2", None)
	if user_has_shop(request.user):
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect("tiendas:interface_farmer")
	shop_owner_token = signing.dumps({"owner_user_id": request.user.id})
	return render(request, "tiendas/create-shop.html", {
		"shop_owner_token": shop_owner_token,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"valores": {},
		"shop_flow_id": flow_id,
	})


@never_cache
def interface_farmer(request):
	"""Renderiza el panel principal del agricultor con sus productos activos."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")
	if not user_has_shop(request.user):
		return redirect("usuarios:home_customer")

	productos = Product.objects.filter(owner=request.user, is_active=True, stock__gt=0).prefetch_related("images").order_by("-created_at")

	# Lógica de mensaje importante admin
	from Mensajes.models import AdminToUserMessage
	from usuarios.models import Register
	register_user = Register.objects.filter(id_usuario=request.user.id).first()
	if not register_user:
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		register_user = Register.objects.filter(numero_documento=request.user.username).first()
	mensaje_admin = None
	if register_user:
		mensaje_admin = AdminToUserMessage.objects.filter(usuario=register_user, leido=False).order_by('-creado').first()

	return render(request, "tiendas/interface_farmer.html", {
		"productos": productos,
		"mensaje_admin": mensaje_admin,
	})


@never_cache
def review_product_farmer(request, product_id):
	"""Redireccion de compatibilidad al detalle de producto del agricultor."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	return redirect("productos:review_product_farmer", product_id=product_id)


@require_POST
@never_cache
def disable_product_farmer(request, product_id):
	"""Desactiva un producto del agricultor desde el panel de tienda."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(Product, pk=product_id, owner=request.user)
	product.is_active = False
	product.save(update_fields=["is_active"])

	return redirect("tiendas:interface_farmer")


@never_cache
def profile_shop(request):
	"""Muestra el perfil de la tienda asociada al usuario autenticado."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	register_user = _get_register_user(request)
	shop = Shop.objects.filter(owner=request.user, is_active=True).order_by("-created_at").first()
	if not shop:
		shop = Shop.objects.filter(owner=request.user).order_by("-created_at").first()
	# Control de flujo y validación de condiciones del proceso.
	if not shop:
		return redirect("usuarios:home_customer")

	return render(request, "tiendas/profile_shop.html", {
		"register_user": register_user,
		"shop": shop,
	})


@require_POST
@never_cache
def disable_shop(request):
	"""Desactiva la tienda activa y deshabilita sus productos asociados."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	shop_id = request.POST.get("shop_id")
	shop_qs = Shop.objects.filter(owner=request.user, is_active=True)
	if shop_id:
		shop_qs = shop_qs.filter(id=shop_id)

	shop = shop_qs.order_by("-created_at").first()
	if not shop:
		return redirect("tiendas:profile_shop")

	shop.is_active = False
	shop.save(update_fields=["is_active"])

	Product.objects.filter(shop=shop).update(is_active=False)
	request.session["force_customer_home"] = True
	request.session["customer_home_notice"] = "Tu tienda fue deshabilitada correctamente."

	return redirect("usuarios:home_customer")


@require_POST
@never_cache
def activate_shop(request):
	"""Reactiva una tienda inactiva del usuario autenticado."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	shop_id = request.POST.get("shop_id")
	shop_qs = Shop.objects.filter(owner=request.user, is_active=False)
	if shop_id:
		shop_qs = shop_qs.filter(id=shop_id)

	shop = shop_qs.order_by("-created_at").first()
	if not shop:
		return redirect("usuarios:home_customer")

	shop.is_active = True
	shop.save(update_fields=["is_active"])

	return redirect("tiendas:interface_farmer")


@never_cache
def mensajes_farmer(request):
	"""Redireccion al modulo de mensajes del agricultor."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	return redirect("mensajes:farmer_messages")


@never_cache
def seller_profile(request, shop_id):
	"""Muestra el perfil publico de un vendedor y sus productos activos."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	shop = get_object_or_404(Shop, id=shop_id, is_active=True)
	register_user = Register.objects.filter(id_usuario=shop.owner_id).first()
	back_url = (request.GET.get("next") or "").strip()
	if not back_url.startswith("/"):
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		back_url = reverse("usuarios:home_customer")
	productos = (
		Product.objects.filter(shop=shop, is_active=True, stock__gt=0)
		.prefetch_related("images")
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		.order_by("-created_at")
	)
	return render(request, "tiendas/seller_profile.html", {
		"shop": shop,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"register_user": register_user,
		"productos": productos,
		"back_url": back_url,
	})


@never_cache
def create_product(request):
	"""Redireccion de compatibilidad al paso 1 de creacion de producto."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	return redirect("productos:create_product")


@never_cache
def create_product2(request):
	"""Redireccion de compatibilidad al paso 2 de creacion de producto."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	return redirect("productos:create_product2")


@never_cache
def create_shop_step1(request):
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	"""Procesa el primer paso de creacion de tienda.

	Guarda en sesion los datos base (nombre, contacto y ubicacion) para
	completar el alta en el segundo paso.
	"""
	# 1) Resuelve propietario del flujo (sesion o token firmado).
	flow_owner = _get_shop_flow_owner(request)
	if not flow_owner and request.method == "GET":
		flow_owner = _resolve_owner_from_token(request.GET.get("owner_token", ""))
		if flow_owner:
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			request.session["shop_flow_owner_id"] = flow_owner.id
	flow_id = request.session.get("shop_flow_id")
	if request.method == "GET" and not flow_id:
		flow_id = uuid.uuid4().hex
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		request.session["shop_flow_id"] = flow_id
	elif not flow_id:
		flow_id = uuid.uuid4().hex
		request.session["shop_flow_id"] = flow_id
	# Control de flujo y validación de condiciones del proceso.
	if not flow_owner and request.method == "POST":
		flow_owner = _resolve_owner_from_token(request.POST.get("owner_token", ""))
		if flow_owner:
			request.session["shop_flow_owner_id"] = flow_owner.id

	if not flow_owner:
		return redirect("tiendas:create_farmer_perfil")
	if user_has_shop(flow_owner):
		return redirect("tiendas:interface_farmer")

	allowed_departamentos = {"Risaralda", "Caldas", "Quindio"}

	# 2) Captura y valida datos base del formulario de tienda.
	if request.method == "POST":
		nombre = request.POST.get("nombre", "").strip()
		telefono = request.POST.get("telefono", "").strip()
		email = request.POST.get("email", "").strip()
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		departamento = request.POST.get("departamento", "").strip()
		municipio = request.POST.get("municipio", "").strip()

		errores = {}
		if not nombre:
			errores["nombre"] = "El nombre de la tienda es obligatorio."
		elif len(nombre) > 50:
			errores["nombre"] = "El nombre de la tienda no puede superar 50 caracteres."
		elif not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]+", nombre):
			errores["nombre"] = "El nombre de la tienda solo puede contener letras y espacios."

		if not telefono:
			errores["telefono"] = "El telefono es obligatorio."
		elif not telefono.isdigit() or len(telefono) != 10:
			errores["telefono"] = "El telefono debe tener 10 digitos."

		if not email:
			errores["email"] = "El correo es obligatorio."
		else:
			try:
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				validate_email(email)
			except ValidationError:
				errores["email"] = "Correo invalido."

		if not departamento:
			errores["departamento"] = "Selecciona un departamento."
		elif departamento not in allowed_departamentos:
			errores["departamento"] = "Selecciona un departamento valido."

		if not municipio:
			errores["municipio"] = "Selecciona un municipio."

		valores = {
			"nombre": nombre,
			"telefono": telefono,
			"email": email,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"departamento": departamento,
			"municipio": municipio,
		}

		if errores:
			shop_owner_token = signing.dumps({"owner_user_id": flow_owner.id})
			return render(request, "tiendas/create-shop.html", {
				"shop_owner_token": shop_owner_token,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"valores": valores,
				"errores": errores,
				"shop_flow_id": flow_id,
			})

		# 3) Persiste paso 1 en sesion para continuar en el paso 2.
		request.session["shop_step1"] = {
			"owner_user_id": flow_owner.id,
			"nombre": nombre,
			"telefono": telefono,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"email": email,
			"departamento": departamento,
			"municipio": municipio,
		}
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect("tiendas:create_shop_step2")

	shop_owner_token = signing.dumps({"owner_user_id": flow_owner.id})
	step1_session = request.session.get("shop_step1", {})
	valores = {}
	if step1_session and step1_session.get("owner_user_id") == flow_owner.id:
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		valores = {
			"nombre": step1_session.get("nombre", ""),
			"telefono": step1_session.get("telefono", ""),
			"email": step1_session.get("email", ""),
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"departamento": step1_session.get("departamento", ""),
			"municipio": step1_session.get("municipio", ""),
		}
	return render(request, "tiendas/create-shop.html", {
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"shop_owner_token": shop_owner_token,
		"valores": valores,
		"shop_flow_id": flow_id,
	})


@never_cache
def create_shop_step2(request):
    # Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
    # Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	"""Completa la creacion de tienda con datos operativos adicionales.

	Valida horarios y direccion cuando hay punto fisico, crea la tienda,
	limpia la sesion del flujo y finaliza redirigiendo al login.
	"""
	# 1) Recupera contexto del paso 1 y propietario del flujo.
	step1 = request.session.get("shop_step1")
	flow_id = request.session.get("shop_flow_id", "")
	owner_user_id = step1.get("owner_user_id") if step1 else request.session.get("shop_flow_owner_id")
	owner_user = User.objects.filter(id=owner_user_id).first() if owner_user_id else None
	# Actualización de estado intermedio que será utilizada en pasos posteriores.
	request_owner_token = request.POST.get("owner_token", "") if request.method == "POST" else request.GET.get("owner_token", "")
	if not owner_user and request_owner_token:
		owner_user = _resolve_owner_from_token(request_owner_token)
		if owner_user:
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			request.session["shop_flow_owner_id"] = owner_user.id
	flow_user = request.user if request.user.is_authenticated else owner_user
	shop_owner_token = signing.dumps({"owner_user_id": owner_user.id}) if owner_user else ""

	if flow_user and user_has_shop(flow_user) and not step1:
		return redirect("tiendas:interface_farmer")
	# Si se pierde sesion del paso 1, redirige de forma segura al inicio del flujo.
	if request.method == "GET" and not step1:
		step1_url = reverse("tiendas:create_shop_step1")
		if shop_owner_token:
			query = urlencode({"owner_token": shop_owner_token})
			# Retorno de respuesta según el estado y resultado de la operación.
			return redirect(f"{step1_url}?{query}")
		return redirect(step1_url)

	errores = {}
	valores = request.session.get("shop_step2", {}).copy() or {
		"tiene_punto_fisico": "no",
		"hora_apertura": "",
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"hora_cierre": "",
		"direccion": "",
		"descripcion": "",
	}

	# 2) Valida reglas operativas (horario/direccion) y aplica consistencia de owner.
	if request.method == "POST":
		if not step1:
			return redirect("tiendas:create_shop_step1")
		if not owner_user:
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			owner_user = _resolve_owner_from_token(request.POST.get("owner_token", ""))
			if owner_user:
				request.session["shop_flow_owner_id"] = owner_user.id
				shop_owner_token = signing.dumps({"owner_user_id": owner_user.id})
		# Control de flujo y validación de condiciones del proceso.
		if not owner_user:
			request.session.pop("shop_step1", None)
			return redirect("usuarios:login")
		if request.user.is_authenticated and step1.get("owner_user_id") != request.user.id:
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			request.session.pop("shop_step1", None)
			return redirect("tiendas:create_shop_step1")

		tiene_punto_fisico = request.POST.get("tiene_punto_fisico", "no").strip()
		usa_punto_fisico = tiene_punto_fisico == "si"
		action = request.POST.get("action", "submit").strip()

		hora_apertura = request.POST.get("hora_apertura", "").strip()
		hora_cierre = request.POST.get("hora_cierre", "").strip()
		direccion = request.POST.get("direccion", "").strip()
		descripcion = request.POST.get("descripcion", "").strip()

		valores = {
			"tiene_punto_fisico": tiene_punto_fisico,
			"hora_apertura": hora_apertura,
			"hora_cierre": hora_cierre,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"direccion": direccion,
			"descripcion": descripcion,
		}
		request.session["shop_step2"] = valores

		if action == "back":
			step1_url = reverse("tiendas:create_shop_step1")
			if shop_owner_token:
				query = urlencode({"owner_token": shop_owner_token})
				# Retorno de respuesta según el estado y resultado de la operación.
				return redirect(f"{step1_url}?{query}")
			return redirect(step1_url)

		horario = ""
		if usa_punto_fisico:
			if not hora_apertura or not hora_cierre:
				errores["horario"] = "Debes ingresar la hora de apertura y cierre."

			if "horario" not in errores:
				try:
					apertura_dt = datetime.strptime(hora_apertura, "%H:%M")
					cierre_dt = datetime.strptime(hora_cierre, "%H:%M")
				# Control de flujo y validación de condiciones del proceso.
				except ValueError:
					errores["horario"] = "Formato de horario invalido."

			if "horario" not in errores and cierre_dt <= apertura_dt:
				errores["horario"] = "La hora de cierre debe ser mayor que la de apertura."

			if not direccion:
				errores["direccion"] = "La direccion de la tienda es obligatoria si tienes punto fisico."

			if "horario" not in errores:
				horario = f"{hora_apertura} - {hora_cierre}"
		else:
			horario = "No aplica"
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			direccion = None

		if errores:
			return render(request, "tiendas/create-shop2.html", {
				"errores": errores,
				"valores": valores,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"shop_flow_id": flow_id,
				"shop_owner_token": shop_owner_token,
			})

		# 3) Crea tienda definitiva con datos combinados de ambos pasos.
		Shop.objects.create(
			owner=owner_user,
			nombre=step1["nombre"],
			telefono=step1["telefono"],
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			email=step1["email"],
			departamento=step1["departamento"],
			municipio=step1["municipio"],
			punto_fisico=usa_punto_fisico,
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			horario=horario,
			direccion=direccion,
			descripcion=descripcion,
		)

		# 4) Limpia sesion del wizard y cierra sesion para forzar relogin limpio.
		del request.session["shop_step1"]
		request.session.pop("shop_step2", None)
		request.session.pop("shop_flow_owner_id", None)
		request.session.pop("shop_flow_id", None)
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		logout(request)
		return redirect(f"{reverse('usuarios:login')}?shop_created=1")

	return render(request, "tiendas/create-shop2.html", {
		"errores": errores,
		"valores": valores,
		"shop_flow_id": flow_id,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"shop_owner_token": shop_owner_token,
	})


@never_cache
def update_shop_step1(request):
	"""Captura el primer paso de actualizacion de una tienda existente."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	shop = Shop.objects.filter(owner=request.user).order_by("-created_at").first()
	if not shop:
		return redirect("tiendas:create_shop_step1")

	errores = {}
	valores = {
		"nombre": shop.nombre or "",
		"telefono": shop.telefono or "",
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"email": shop.email or "",
		"departamento": shop.departamento or "",
		"municipio": shop.municipio or "",
	}

	step1_session = request.session.get("update_shop_step1")
	if step1_session:
		valores.update(step1_session)

	if request.method == "POST":
		nombre = request.POST.get("nombre", "").strip()
		telefono = request.POST.get("telefono", "").strip()
		email = request.POST.get("email", "").strip()
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		departamento = request.POST.get("departamento", "").strip()
		municipio = request.POST.get("municipio", "").strip()

		valores = {
			"nombre": nombre,
			"telefono": telefono,
			"email": email,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"departamento": departamento,
			"municipio": municipio,
		}

		if not nombre:
			errores["nombre"] = "El nombre de la tienda es obligatorio."
		if not telefono:
			errores["telefono"] = "El telefono es obligatorio."
		# Control de flujo y validación de condiciones del proceso.
		if not email:
			errores["email"] = "El correo electronico es obligatorio."
		if not departamento:
			errores["departamento"] = "El departamento es obligatorio."
		# Control de flujo y validación de condiciones del proceso.
		if not municipio:
			errores["municipio"] = "El municipio es obligatorio."

		if errores:
			return render(request, "tiendas/update_shop.html", {
				"shop": shop,
				"errores": errores,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"valores": valores,
			})

		request.session["update_shop_step1"] = valores
		return redirect("tiendas:update_shop_step2")

	return render(request, "tiendas/update_shop.html", {
		"shop": shop,
		"errores": errores,
		"valores": valores,
	# Paso de apoyo dentro del flujo principal de la funcionalidad.
	})


@never_cache
def update_shop_step2(request):
	"""Aplica el segundo paso de actualizacion y guarda cambios finales."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	shop = Shop.objects.filter(owner=request.user).order_by("-created_at").first()
	if not shop:
		return redirect("tiendas:create_shop_step1")

	step1 = request.session.get("update_shop_step1", {})
	if not step1:
		step1 = {
			"nombre": shop.nombre or "",
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"telefono": shop.telefono or "",
			"email": shop.email or "",
			"departamento": shop.departamento or "",
			"municipio": shop.municipio or "",
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		}

	errores = {}
	valores = {
		"tiene_punto_fisico": "si" if shop.punto_fisico else "no",
		"horario": shop.horario or "",
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"url": "",
		"direccion": shop.direccion or "",
		"descripcion": shop.descripcion or "",
	}

	if request.method == "POST":
		tiene_punto_fisico = request.POST.get("tiene_punto_fisico", "si").strip()
		usa_punto_fisico = tiene_punto_fisico == "si"
		horario = request.POST.get("horario", "").strip()
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		direccion = request.POST.get("direccion", "").strip()
		descripcion = request.POST.get("descripcion", "").strip()
		url = request.POST.get("url", "").strip()

		valores = {
			"tiene_punto_fisico": tiene_punto_fisico,
			"horario": horario,
			"url": url,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"direccion": direccion,
			"descripcion": descripcion,
		}

		if usa_punto_fisico:
			if not horario:
				errores["horario"] = "El horario es obligatorio si tienes punto fisico."
			if not direccion:
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				errores["direccion"] = "La direccion es obligatoria si tienes punto fisico."
		else:
			horario = "No aplica"
			direccion = None

		if errores:
			return render(request, "tiendas/update_shop2.html", {
				"shop": shop,
				"errores": errores,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"valores": valores,
			})

		shop.nombre = step1.get("nombre", shop.nombre)
		shop.telefono = step1.get("telefono", shop.telefono)
		shop.email = step1.get("email", shop.email)
		shop.departamento = step1.get("departamento", shop.departamento)
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		shop.municipio = step1.get("municipio", shop.municipio)
		shop.punto_fisico = usa_punto_fisico
		shop.horario = horario
		shop.direccion = direccion
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		shop.descripcion = descripcion
		shop.save()

		request.session.pop("update_shop_step1", None)
		return redirect("tiendas:interface_farmer")

	return render(request, "tiendas/update_shop2.html", {
		"shop": shop,
		"errores": errores,
		"valores": valores,
	# Paso de apoyo dentro del flujo principal de la funcionalidad.
	})
