from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.files import File
from django.urls import reverse
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError

import os

from Tiendas.models import Shop

from .models import Product, ProductImage

# Create your views here.


def _temp_product_dir():
	temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_productos")
	os.makedirs(temp_dir, exist_ok=True)
	return temp_dir


def _remove_temp_files(paths):
	for path in paths or []:
		try:
			if path and os.path.exists(path):
				os.remove(path)
		except OSError:
			pass


def _validate_step1(data, files):
	errors = {}

	nombre = (data.get("nombre") or "").strip()
	tipo = (data.get("tipo") or "").strip()
	tipo_otro = (data.get("tipo_otro") or "").strip()
	unidad = (data.get("unidad") or "").strip()

	if not files:
		errors["fotos"] = "Debes cargar al menos una imagen."
	elif len(files) > 8:
		errors["fotos"] = "Solo puedes cargar máximo 8 imágenes."
	else:
		for photo in files:
			if not (photo.content_type or "").startswith("image/"):
				errors["fotos"] = "Solo se permiten archivos de imagen."
				break

	if not nombre:
		errors["nombre"] = "El nombre del producto es obligatorio."
	elif len(nombre) < 3:
		errors["nombre"] = "El nombre debe tener al menos 3 caracteres."

	tipos_validos = {choice[0] for choice in Product.TIPO_CHOICES}
	if tipo not in tipos_validos:
		errors["tipo"] = "Selecciona un tipo de producto válido."

	if tipo == Product.TIPO_OTROS:
		if not tipo_otro:
			errors["tipo_otro"] = "Escribe el tipo de producto."
		elif len(tipo_otro) < 3:
			errors["tipo_otro"] = "Debe tener al menos 3 caracteres."

	unidades_validas = {choice[0] for choice in Product.UNIDAD_CHOICES}
	if unidad not in unidades_validas:
		errors["unidad"] = "Selecciona una unidad de medida válida."
	else:
		permitidas = Product.UNIDADES_POR_TIPO.get(tipo, set())
		if tipo and unidad not in permitidas:
			errors["unidad"] = f"La unidad no aplica para {tipo}."

	return errors


def _validate_step2(data):
	errors = {}

	precio_raw = (data.get("precio") or "").strip()
	descripcion = (data.get("descripcion") or "").strip()
	garantia = (data.get("garantia") or "").strip()

	precio_value = None
	if not precio_raw:
		errors["precio"] = "El precio es obligatorio."
	else:
		try:
			precio_value = Decimal(precio_raw)
		except InvalidOperation:
			errors["precio"] = "Ingresa un precio válido mayor que 0."
		else:
			if precio_value <= 0:
				errors["precio"] = "Ingresa un precio válido mayor que 0."

	if not descripcion:
		errors["descripcion"] = "La descripción es obligatoria."
	elif len(descripcion) < 10:
		errors["descripcion"] = "La descripción debe tener al menos 10 caracteres."

	if not garantia:
		errors["garantia"] = "El tiempo de durabilidad es obligatorio."
	elif len(garantia) < 3:
		errors["garantia"] = "El tiempo de durabilidad debe tener al menos 3 caracteres."

	return errors, precio_value


@never_cache
def create_product(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	if request.method == "POST":
		photos = request.FILES.getlist("fotos")
		errors = _validate_step1(request.POST, photos)

		valores = {
			"nombre": (request.POST.get("nombre") or "").strip(),
			"tipo": (request.POST.get("tipo") or "").strip(),
			"tipo_otro": (request.POST.get("tipo_otro") or "").strip(),
			"unidad": (request.POST.get("unidad") or "").strip(),
		}

		if errors:
			return render(request, "productos/create_product.html", {
				"errores": errors,
				"valores": valores,
			})

		old_paths = request.session.get("product_temp_images", [])
		_remove_temp_files(old_paths)

		temp_dir = _temp_product_dir()
		temp_paths = []
		for photo in photos:
			safe_name = f"{request.user.id}_{photo.name}"
			temp_path = os.path.join(temp_dir, safe_name)
			base_name, ext = os.path.splitext(temp_path)
			counter = 1
			while os.path.exists(temp_path):
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
	return render(request, "productos/create_product.html", {"valores": valores})


@never_cache
def create_product2(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product_success = request.session.pop("product_success", False)
	if request.method == "GET" and product_success:
		return render(request, "productos/create_product2.html", {
			"product_success": True,
			"flash_redirect_url": reverse("tiendas:interface_farmer"),
		})

	step1 = request.session.get("product_step1")
	temp_paths = request.session.get("product_temp_images", [])

	if not step1:
		return redirect("productos:create_product")

	if request.method == "POST":
		errors, precio_value = _validate_step2(request.POST)
		valores = {
			"precio": (request.POST.get("precio") or "").strip(),
			"descripcion": (request.POST.get("descripcion") or "").strip(),
			"garantia": (request.POST.get("garantia") or "").strip(),
		}

		if not temp_paths:
			errors["fotos"] = "Debes volver al paso 1 y cargar imágenes del producto."

		if errors:
			return render(request, "productos/create_product2.html", {
				"errores": errors,
				"valores": valores,
			})

		shop = Shop.objects.filter(owner=request.user).first()

		product = Product.objects.create(
			owner=request.user,
			shop=shop,
			nombre=step1.get("nombre", ""),
			tipo=step1.get("tipo", ""),
			tipo_otro=step1.get("tipo_otro", ""),
			unidad=step1.get("unidad", ""),
			precio=precio_value,
			descripcion=valores["descripcion"],
			garantia=valores["garantia"],
			metodo_pago=Product.METODO_PAGO_CONTADO,
			metodo_entrega=Product.METODO_ENTREGA_DOMICILIO,
		)

		for temp_path in temp_paths:
			if not os.path.exists(temp_path):
				continue
			filename = os.path.basename(temp_path)
			with open(temp_path, "rb") as img_stream:
				ProductImage.objects.create(
					product=product,
					image=File(img_stream, name=filename),
				)

		_remove_temp_files(temp_paths)
		request.session.pop("product_step1", None)
		request.session.pop("product_temp_images", None)
		request.session["product_success"] = True
		return redirect("productos:create_product2")

	return render(request, "productos/create_product2.html")


@never_cache
def descripcion_product(request, product_id):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(
		Product.objects.select_related("shop", "owner").prefetch_related("images"),
		pk=product_id,
	)

	if (not product.is_active or (product.shop and not product.shop.is_active)) and product.owner_id != request.user.id:
		return redirect("usuarios:home_customer")

	return render(request, "productos/descripcion_product.html", {
		"product": product,
	})


@never_cache
def review_product_farmer(request, product_id):
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
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(Product, pk=product_id, owner=request.user)
	product.is_active = False
	product.save(update_fields=["is_active"])

	return redirect("tiendas:interface_farmer")


@never_cache
def disabled_products(request):
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
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(Product, pk=product_id, owner=request.user, is_active=False)
	product.is_active = True
	product.save(update_fields=["is_active"])

	return redirect("productos:disabled_products")


@never_cache
def update_product(request, product_id):
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
		"unidad": product.unidad,
		"precio": str(product.precio),
		"descripcion": product.descripcion,
		"garantia": product.garantia,
		"metodo_pago": product.metodo_pago,
		"metodo_entrega": product.metodo_entrega,
	}

	if request.method == "POST":
		delete_image_ids = request.POST.getlist("delete_images")
		new_images = request.FILES.getlist("new_images")

		valores = {
			"nombre": (request.POST.get("nombre") or "").strip(),
			"tipo": (request.POST.get("tipo") or "").strip(),
			"tipo_otro": (request.POST.get("tipo_otro") or "").strip(),
			"unidad": (request.POST.get("unidad") or "").strip(),
			"precio": (request.POST.get("precio") or "").strip(),
			"descripcion": (request.POST.get("descripcion") or "").strip(),
			"garantia": (request.POST.get("garantia") or "").strip(),
			"metodo_pago": (request.POST.get("metodo_pago") or "").strip(),
			"metodo_entrega": (request.POST.get("metodo_entrega") or "").strip(),
		}

		try:
			precio_value = Decimal(valores["precio"])
		except (InvalidOperation, ValueError):
			errores["precio"] = "Ingresa un precio valido mayor que 0."
			precio_value = None

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
		elif total_after_update > 8:
			errores["fotos"] = "Solo puedes mantener máximo 8 imágenes por producto."

		if not errores:
			product.nombre = valores["nombre"]
			product.tipo = valores["tipo"]
			product.tipo_otro = valores["tipo_otro"]
			product.unidad = valores["unidad"]
			product.precio = precio_value
			product.descripcion = valores["descripcion"]
			product.garantia = valores["garantia"]
			product.metodo_pago = valores["metodo_pago"]
			product.metodo_entrega = valores["metodo_entrega"]

			try:
				product.full_clean()
			except ValidationError as exc:
				for field, messages in exc.message_dict.items():
					errores[field] = messages[0] if messages else "Valor invalido."
			else:
				product.save()
				if delete_qs.exists():
					delete_qs.delete()

				for image_file in new_images:
					ProductImage.objects.create(product=product, image=image_file)

				return redirect("productos:review_product_farmer", product_id=product.id)

	return render(request, "productos/update_product.html", {
		"product": product,
		"existing_images": existing_images,
		"existing_images_count": existing_count,
		"can_upload_more_images": existing_count < 8,
		"valores": valores,
		"errores": errores,
		"tipo_choices": Product.TIPO_CHOICES,
		"unidad_choices": Product.UNIDAD_CHOICES,
		"metodo_pago_choices": Product.METODO_PAGO_CHOICES,
		"metodo_entrega_choices": Product.METODO_ENTREGA_CHOICES,
	})
