"""
Vistas del modulo de productos.

Este archivo implementa el ciclo completo de gestion de productos para agricultores:
- Creacion en dos pasos (datos basicos + datos comerciales).
- Validaciones de negocio (stock, precio, unidades y formatos permitidos).
- Manejo de imagenes temporales y definitivas.
- Activacion/desactivacion de productos.
- Solicitudes al administrador para reactivar productos bloqueados.
- Edicion de productos con control de cantidad maxima/minima de imagenes.

Reglas clave del modulo:
- Un producto debe tener al menos una imagen y como maximo 8.
- El producto se marca inactivo automaticamente cuando el stock llega a 0.
- Si un producto fue deshabilitado por administracion, el agricultor no puede
	reactivarlo directamente y debe enviar una solicitud.
"""

from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
# Importación de dependencias necesarias para ejecutar esta vista.
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.core.files import File
# Importación de dependencias necesarias para ejecutar esta vista.
from django.urls import reverse
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
import re

import os

from Tiendas.models import Shop

from .models import Product, ProductImage


PRODUCT_NAME_ALLOWED_RE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s.,\-]+$")
PRODUCT_GUARANTEE_ALLOWED_RE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s.,:/%\-]+$")

# Create your views here.


def _temp_product_dir():
	"""Retorna la ruta temporal para imagenes de producto y la garantiza existente."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_productos")
	os.makedirs(temp_dir, exist_ok=True)
	return temp_dir


def _remove_temp_files(paths):
	"""Elimina archivos temporales de forma segura ignorando errores de E/S."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	for path in paths or []:
		try:
			if path and os.path.exists(path):
				os.remove(path)
		# Control de flujo y validación de condiciones del proceso.
		except OSError:
			pass


def _validate_step1(data, files, allow_existing_images=False):
	"""Valida datos del paso 1 (identidad del producto e imagenes)."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	errors = {}

	nombre = (data.get("nombre") or "").strip()
	tipo = (data.get("tipo") or "").strip()
	tipo_otro = (data.get("tipo_otro") or "").strip()
	unidad = (data.get("unidad") or "").strip()

	if not files and not allow_existing_images:
		errors["fotos"] = "Debes cargar al menos una imagen."
	elif len(files) > 8:
		errors["fotos"] = "Solo puedes cargar máximo 8 imágenes."
	# Control de flujo y validación de condiciones del proceso.
	else:
		for photo in files:
			if not (photo.content_type or "").startswith("image/"):
				errors["fotos"] = "Solo se permiten archivos de imagen."
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				break

	if not nombre:
		errors["nombre"] = "El nombre del producto es obligatorio."
	elif len(nombre) < 3:
		errors["nombre"] = "El nombre debe tener al menos 3 caracteres."
	# Control de flujo y validación de condiciones del proceso.
	elif len(nombre) > 120:
		errors["nombre"] = "El nombre no debe superar 120 caracteres."
	elif not PRODUCT_NAME_ALLOWED_RE.fullmatch(nombre):
		errors["nombre"] = "El nombre contiene caracteres no permitidos."

	tipos_validos = {choice[0] for choice in Product.TIPO_CHOICES}
	if tipo not in tipos_validos:
		errors["tipo"] = "Selecciona un tipo de producto válido."

	if tipo == Product.TIPO_OTROS:
		if not tipo_otro:
			errors["tipo_otro"] = "Escribe el tipo de producto."
		elif len(tipo_otro) < 3:
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			errors["tipo_otro"] = "Debe tener al menos 3 caracteres."

	unidades_validas = {choice[0] for choice in Product.UNIDAD_CHOICES}
	if unidad not in unidades_validas:
		errors["unidad"] = "Selecciona una unidad de medida válida."
	else:
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		permitidas = Product.UNIDADES_POR_TIPO.get(tipo, set())
		if tipo and unidad not in permitidas:
			errors["unidad"] = f"La unidad no aplica para {tipo}."

	return errors


def _validate_step2(data):
	"""Valida datos del paso 2 (precio, stock, descripcion y garantia)."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	errors = {}

	precio_raw = (data.get("precio") or "").strip()
	stock_raw = (data.get("stock") or "").strip()
	descripcion = (data.get("descripcion") or "").strip()
	garantia = (data.get("garantia") or "").strip()

	precio_value = None
	stock_value = None
	if not precio_raw:
		errors["precio"] = "El precio es obligatorio."
	# Control de flujo y validación de condiciones del proceso.
	else:
		try:
			precio_value = Decimal(precio_raw)
		except InvalidOperation:
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			errors["precio"] = "Ingresa un precio válido mayor que 0."
		else:
			if precio_value <= 0:
				errors["precio"] = "Ingresa un precio válido mayor que 0."

	if not stock_raw:
		errors["stock"] = "La cantidad disponible es obligatoria."
	else:
		try:
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			stock_value = int(stock_raw)
		except (TypeError, ValueError):
			errors["stock"] = "Ingresa una cantidad disponible válida."
		else:
			# Control de flujo y validación de condiciones del proceso.
			if stock_value < 1:
				errors["stock"] = "La cantidad disponible debe ser al menos 1."

	if not descripcion:
		errors["descripcion"] = "La descripción es obligatoria."
	elif len(descripcion) < 10:
		errors["descripcion"] = "La descripción debe tener al menos 10 caracteres."
	# Control de flujo y validación de condiciones del proceso.
	elif len(descripcion) > 255:
		errors["descripcion"] = "La descripción no debe superar 255 caracteres."

	if not garantia:
		errors["garantia"] = "El tiempo de durabilidad es obligatorio."
	elif len(garantia) < 3:
		errors["garantia"] = "El tiempo de durabilidad debe tener al menos 3 caracteres."
	# Control de flujo y validación de condiciones del proceso.
	elif len(garantia) > 120:
		errors["garantia"] = "La garantía no debe superar 120 caracteres."
	elif not PRODUCT_GUARANTEE_ALLOWED_RE.fullmatch(garantia):
		errors["garantia"] = "La garantía contiene caracteres no permitidos."

	return errors, precio_value, stock_value


@never_cache
def create_product(request):
	"""Gestiona el paso 1 de creacion de producto con imagenes temporales."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	if request.method == "POST":
		photos = request.FILES.getlist("fotos")
		existing_temp_paths = request.session.get("product_temp_images", [])
		errors = _validate_step1(request.POST, photos, allow_existing_images=bool(existing_temp_paths))

		valores = {
			"nombre": (request.POST.get("nombre") or "").strip(),
			"tipo": (request.POST.get("tipo") or "").strip(),
			"tipo_otro": (request.POST.get("tipo_otro") or "").strip(),
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"unidad": (request.POST.get("unidad") or "").strip(),
		}

		if errors:
			return render(request, "productos/create_product.html", {
				"errores": errors,
				"valores": valores,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"existing_temp_images_count": len(existing_temp_paths),
			})

		temp_paths = existing_temp_paths
		if photos:
			old_paths = request.session.get("product_temp_images", [])
			_remove_temp_files(old_paths)

			temp_dir = _temp_product_dir()
			temp_paths = []
			for photo in photos:
				safe_name = f"{request.user.id}_{photo.name}"
				# Actualización de estado intermedio que será utilizada en pasos posteriores.
				temp_path = os.path.join(temp_dir, safe_name)
				base_name, ext = os.path.splitext(temp_path)
				counter = 1
				while os.path.exists(temp_path):
					# Actualización de estado intermedio que será utilizada en pasos posteriores.
					temp_path = f"{base_name}_{counter}{ext}"
					counter += 1

				with open(temp_path, "wb") as temp_file:
					for chunk in photo.chunks():
						temp_file.write(chunk)
				temp_paths.append(temp_path)

		request.session["product_step1"] = valores
		request.session["product_temp_images"] = temp_paths
		return redirect("productos:create_product2")

	valores = request.session.get("product_step1", {})
	existing_temp_images_count = len(request.session.get("product_temp_images", []))
	return render(request, "productos/create_product.html", {
		"valores": valores,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"existing_temp_images_count": existing_temp_images_count,
	})


@never_cache
def create_product2(request):
	"""Gestiona el paso 2 y persiste el producto con sus imagenes finales."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product_success = request.session.pop("product_success", False)
	if request.method == "GET" and product_success:
		return render(request, "productos/create_product2.html", {
			"product_success": True,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"flash_redirect_url": reverse("tiendas:interface_farmer"),
		})

	step1 = request.session.get("product_step1")
	temp_paths = request.session.get("product_temp_images", [])

	if not step1:
		return redirect("productos:create_product")

	if request.method == "POST":
		errors, precio_value, stock_value = _validate_step2(request.POST)
		valores = {
			"precio": (request.POST.get("precio") or "").strip(),
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"stock": (request.POST.get("stock") or "").strip(),
			"descripcion": (request.POST.get("descripcion") or "").strip(),
			"garantia": (request.POST.get("garantia") or "").strip(),
		}

		if not temp_paths:
			errors["fotos"] = "Debes volver al paso 1 y cargar imágenes del producto."

		if errors:
			return render(request, "productos/create_product2.html", {
				"errores": errors,
				"valores": valores,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			})

		shop = Shop.objects.filter(owner=request.user).first()

		product = Product(
			owner=request.user,
			shop=shop,
			nombre=step1.get("nombre", ""),
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			tipo=step1.get("tipo", ""),
			tipo_otro=step1.get("tipo_otro", ""),
			unidad=step1.get("unidad", ""),
			precio=precio_value,
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			stock=stock_value,
			descripcion=valores["descripcion"],
			garantia=valores["garantia"],
			is_active=stock_value > 0,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		)

		try:
			product.full_clean()
		except ValidationError as exc:
			for field, messages in exc.message_dict.items():
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				errors[field] = messages[0] if messages else "Valor invalido."
			return render(request, "productos/create_product2.html", {
				"errores": errors,
				"valores": valores,
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			})

		product.save()

		for temp_path in temp_paths:
			if not os.path.exists(temp_path):
				continue
			filename = os.path.basename(temp_path)
			# Contexto controlado para garantizar consistencia y liberación segura de recursos.
			with open(temp_path, "rb") as img_stream:
				ProductImage.objects.create(
					product=product,
					image=File(img_stream, name=filename),
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				)

		_remove_temp_files(temp_paths)
		request.session.pop("product_step1", None)
		request.session.pop("product_temp_images", None)
		request.session["product_success"] = True
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect("productos:create_product2")

	return render(request, "productos/create_product2.html")


@never_cache
def descripcion_product(request, product_id):
	"""Muestra la descripcion publica del producto cuando esta disponible."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(
		Product.objects.select_related("shop", "owner").prefetch_related("images"),
		pk=product_id,
	)

	if (
		(not product.is_active or product.stock <= 0 or (product.shop and not product.shop.is_active))
		and product.owner_id != request.user.id
	):
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect("usuarios:home_customer")

	return render(request, "productos/descripcion_product.html", {
		"product": product,
	})


@never_cache
def review_product_farmer(request, product_id):
	"""Muestra al agricultor el detalle de uno de sus productos."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	if not Shop.objects.filter(owner=request.user, is_active=True).exists():
		return redirect("usuarios:home_customer")

	product = get_object_or_404(
		Product.objects.filter(owner=request.user).prefetch_related("images"),
		pk=product_id,
	)

	return render(request, "productos/review_product_farmer.html", {
		"product": product,
	})


@require_POST
@never_cache
def disable_product(request, product_id):
	"""Desactiva un producto del agricultor autenticado."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(Product, pk=product_id, owner=request.user)
	product.is_active = False
	product.disabled_by_admin = False
	product.save(update_fields=["is_active", "disabled_by_admin"])

	return redirect("tiendas:interface_farmer")


@never_cache
def disabled_products(request):
	"""Lista productos inactivos del agricultor para posible reactivacion."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	productos = Product.objects.filter(
		owner=request.user,
		is_active=False,
	).prefetch_related("images").order_by("-created_at")

	return render(request, "productos/p-card_disable.html", {
		"productos": productos,
	})


@require_POST
@never_cache
def activate_product(request, product_id):
	"""Reactiva un producto si no fue bloqueado por admin y tiene stock."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(Product, pk=product_id, owner=request.user, is_active=False)

	if product.disabled_by_admin:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({
				"ok": False,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"requires_admin_message": True,
				"message": "Este producto fue deshabilitado por el administrador.",
			})
		return redirect("productos:disabled_products")

	if product.stock <= 0:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({
				"ok": False,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"message": "No puedes habilitar este producto porque su stock es 0.",
			}, status=400)
		return redirect("productos:disabled_products")

	product.is_active = True
	product.save(update_fields=["is_active"])

	return redirect("productos:disabled_products")


@require_POST
@never_cache
def request_admin_product_reactivation(request, product_id):
	"""Envia una solicitud al admin para reactivar un producto bloqueado."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return JsonResponse({"ok": False, "message": "Sesion no valida."}, status=401)

	product = get_object_or_404(Product, pk=product_id, owner=request.user, is_active=False)
	if not product.disabled_by_admin:
		return JsonResponse({"ok": False, "message": "Este producto no requiere aprobacion del administrador."}, status=400)

	message_text = (request.POST.get("message") or "").strip()
	if len(message_text) < 10:
		return JsonResponse({"ok": False, "message": "Escribe un mensaje de al menos 10 caracteres."}, status=400)

	from Mensajes.models import AdminNotification
	from usuarios.models import Register

	sender_register = Register.objects.filter(id_usuario=request.user.id).first()
	AdminNotification.objects.create(
		notification_type=AdminNotification.TYPE_PRODUCT_REACTIVATION,
		sender_user=request.user,
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		sender_register=sender_register,
		product=product,
		message=message_text,
	)

	return JsonResponse({"ok": True, "message": "Tu solicitud fue enviada al administrador."})


@never_cache
def update_product(request, product_id):
	"""Actualiza datos de un producto y administra sus imagenes asociadas."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(Product, pk=product_id, owner=request.user)
	existing_images = product.images.all().order_by("-created_at")
	existing_count = existing_images.count()
	errores = {}

	valores = {
		"nombre": product.nombre,
		"tipo": product.tipo,
		"tipo_otro": product.tipo_otro or "",
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"unidad": product.unidad,
		"precio": str(product.precio),
		"stock": product.stock,
		"descripcion": product.descripcion,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"garantia": product.garantia,
	}

	if request.method == "POST":
		delete_image_ids = request.POST.getlist("delete_images")
		new_images = request.FILES.getlist("new_images")

		valores = {
			"nombre": (request.POST.get("nombre") or "").strip(),
			"tipo": (request.POST.get("tipo") or "").strip(),
			"tipo_otro": (request.POST.get("tipo_otro") or "").strip(),
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"unidad": (request.POST.get("unidad") or "").strip(),
			"precio": (request.POST.get("precio") or "").strip(),
			"stock": (request.POST.get("stock") or "").strip(),
			"descripcion": (request.POST.get("descripcion") or "").strip(),
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"garantia": (request.POST.get("garantia") or "").strip(),
		}

		try:
			precio_value = Decimal(valores["precio"])
		except (InvalidOperation, ValueError):
			errores["precio"] = "Ingresa un precio valido mayor que 0."
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			precio_value = None
		else:
			if precio_value <= 0:
				errores["precio"] = "Ingresa un precio valido mayor que 0."

		try:
			stock_value = int(valores["stock"])
		except (TypeError, ValueError):
			errores["stock"] = "Ingresa una cantidad disponible válida."
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			stock_value = None
		else:
			if stock_value < 1:
				errores["stock"] = "La cantidad disponible debe ser al menos 1."

		for photo in new_images:
			if not (photo.content_type or "").startswith("image/"):
				errores["fotos"] = "Solo se permiten archivos de imagen."
				break

		delete_qs = product.images.filter(id__in=delete_image_ids)
		remaining_count = existing_count - delete_qs.count()
		total_after_update = remaining_count + len(new_images)

		if existing_count >= 8 and len(new_images) > 0 and delete_qs.count() == 0:
			errores["fotos"] = "Ya tienes 8 imagenes. Elimina alguna para poder subir nuevas."
		elif total_after_update <= 0:
			errores["fotos"] = "El producto debe tener al menos una imagen."
		# Control de flujo y validación de condiciones del proceso.
		elif total_after_update > 8:
			errores["fotos"] = "Solo puedes mantener máximo 8 imágenes por producto."

		if not errores:
			product.nombre = valores["nombre"]
			product.tipo = valores["tipo"]
			product.tipo_otro = valores["tipo_otro"]
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			product.unidad = valores["unidad"]
			product.precio = precio_value
			product.stock = stock_value
			product.descripcion = valores["descripcion"]
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			product.garantia = valores["garantia"]
			if product.stock <= 0:
				product.is_active = False

			try:
				product.full_clean()
			except ValidationError as exc:
				for field, messages in exc.message_dict.items():
					# Paso de apoyo dentro del flujo principal de la funcionalidad.
					errores[field] = messages[0] if messages else "Valor invalido."
			else:
				product.save()
				if delete_qs.exists():
					# Paso de apoyo dentro del flujo principal de la funcionalidad.
					delete_qs.delete()

				for image_file in new_images:
					ProductImage.objects.create(product=product, image=image_file)

				return redirect("productos:review_product_farmer", product_id=product.id)

	return render(request, "productos/update_product.html", {
		"product": product,
		"existing_images": existing_images,
		"existing_images_count": existing_count,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"can_upload_more_images": existing_count < 8,
		"valores": valores,
		"errores": errores,
		"tipo_choices": Product.TIPO_CHOICES,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"unidad_choices": Product.UNIDAD_CHOICES,
	})
