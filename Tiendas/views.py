from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from datetime import datetime

from .models import Shop
from Productos.models import Product
from usuarios.models import Register


def user_has_shop(user):
	if not user or not user.is_authenticated:
		return False
	return Shop.objects.filter(owner=user, is_active=True).exists()


def user_has_inactive_shop(user):
	if not user or not user.is_authenticated:
		return False
	return Shop.objects.filter(owner=user, is_active=False).exists()


def resolve_legacy_tienda_route(page):
	legacy_routes = {
		"create-shop.html": ("redirect", "tiendas:create_farmer_perfil"),
		"create-farmer-perfil.html": ("redirect", "tiendas:create_farmer_perfil"),
		"create-shop2.html": ("redirect", "tiendas:create_shop_step2"),
		"interface_farmer.html": ("redirect", "tiendas:interface_farmer"),
		"profile_shop.html": ("redirect", "tiendas:profile_shop"),
		"p_update_shop.html": ("redirect", "tiendas:update_shop_step1"),
		"p_update_shop2.html": ("redirect", "tiendas:update_shop_step2"),
		"form_subir_producto.html": ("redirect", "productos:create_product"),
		"form_subir_producto2.html": ("redirect", "productos:create_product2"),
	}
	return legacy_routes.get(page)


def _get_register_user(request):
	register_user = Register.objects.filter(id_usuario=request.user.id).first()
	if not register_user:
		register_user = Register.objects.filter(numero_documento=request.user.username).first()
	return register_user


def create_farmer_perfil(request):
	return render(request, "tiendas/create-farmer-perfil.html")


@never_cache
def interface_farmer(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")
	if not user_has_shop(request.user):
		return redirect("usuarios:home_customer")

	productos = Product.objects.filter(owner=request.user, is_active=True).prefetch_related("images").order_by("-created_at")

	return render(request, "tiendas/interface_farmer.html", {
		"productos": productos,
	})


@never_cache
def review_product_farmer(request, product_id):
	return redirect("productos:review_product_farmer", product_id=product_id)


@require_POST
@never_cache
def disable_product_farmer(request, product_id):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	product = get_object_or_404(Product, pk=product_id, owner=request.user)
	product.is_active = False
	product.save(update_fields=["is_active"])

	return redirect("tiendas:interface_farmer")


@never_cache
def profile_shop(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	register_user = _get_register_user(request)
	shop = Shop.objects.filter(owner=request.user, is_active=True).order_by("-created_at").first()
	if not shop:
		shop = Shop.objects.filter(owner=request.user).order_by("-created_at").first()
	if not shop:
		return redirect("usuarios:home_customer")

	return render(request, "tiendas/profile_shop.html", {
		"register_user": register_user,
		"shop": shop,
	})


@require_POST
@never_cache
def disable_shop(request):
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
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	return redirect("mensajes:farmer_messages")


@never_cache
def create_product(request):
	return redirect("productos:create_product")


@never_cache
def create_product2(request):
	return redirect("productos:create_product2")


def create_shop_step1(request):
	if request.method == "POST":
		request.session["shop_step1"] = {
			"nombre": request.POST.get("nombre"),
			"telefono": request.POST.get("telefono"),
			"email": request.POST.get("email"),
			"departamento": request.POST.get("departamento"),
			"municipio": request.POST.get("municipio"),
		}
		return redirect("tiendas:create_shop_step2")

	return render(request, "tiendas/create-shop.html")


def create_shop_step2(request):
	shop_success = request.session.pop("shop_success", False)
	errores = {}
	valores = {
		"tiene_punto_fisico": "no",
		"hora_apertura": "",
		"hora_cierre": "",
		"direccion": "",
		"descripcion": "",
	}

	if request.method == "POST":
		step1 = request.session.get("shop_step1")
		if not step1:
			return redirect("tiendas:create_shop_step1")

		tiene_punto_fisico = request.POST.get("tiene_punto_fisico", "no").strip()
		usa_punto_fisico = tiene_punto_fisico == "si"

		hora_apertura = request.POST.get("hora_apertura", "").strip()
		hora_cierre = request.POST.get("hora_cierre", "").strip()
		direccion = request.POST.get("direccion", "").strip()
		descripcion = request.POST.get("descripcion", "").strip()

		valores = {
			"tiene_punto_fisico": tiene_punto_fisico,
			"hora_apertura": hora_apertura,
			"hora_cierre": hora_cierre,
			"direccion": direccion,
			"descripcion": descripcion,
		}

		horario = ""
		if usa_punto_fisico:
			if not hora_apertura or not hora_cierre:
				errores["horario"] = "Debes ingresar la hora de apertura y cierre."

			if "horario" not in errores:
				try:
					apertura_dt = datetime.strptime(hora_apertura, "%H:%M")
					cierre_dt = datetime.strptime(hora_cierre, "%H:%M")
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
			direccion = None

		if errores:
			return render(request, "tiendas/create-shop2.html", {
				"errores": errores,
				"valores": valores,
				"shop_success": shop_success,
			})

		Shop.objects.create(
			owner=request.user if request.user.is_authenticated else None,
			nombre=step1["nombre"],
			telefono=step1["telefono"],
			email=step1["email"],
			departamento=step1["departamento"],
			municipio=step1["municipio"],
			punto_fisico=usa_punto_fisico,
			horario=horario,
			direccion=direccion,
			descripcion=descripcion,
		)

		del request.session["shop_step1"]

		request.session["shop_success"] = True
		return redirect("tiendas:create_shop_step2")

	return render(request, "tiendas/create-shop2.html", {
		"shop_success": shop_success,
		"errores": errores,
		"valores": valores,
	})


@never_cache
def update_shop_step1(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	shop = Shop.objects.filter(owner=request.user).order_by("-created_at").first()
	if not shop:
		return redirect("tiendas:create_shop_step1")

	errores = {}
	valores = {
		"nombre": shop.nombre or "",
		"telefono": shop.telefono or "",
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
		departamento = request.POST.get("departamento", "").strip()
		municipio = request.POST.get("municipio", "").strip()

		valores = {
			"nombre": nombre,
			"telefono": telefono,
			"email": email,
			"departamento": departamento,
			"municipio": municipio,
		}

		if not nombre:
			errores["nombre"] = "El nombre de la tienda es obligatorio."
		if not telefono:
			errores["telefono"] = "El telefono es obligatorio."
		if not email:
			errores["email"] = "El correo electronico es obligatorio."
		if not departamento:
			errores["departamento"] = "El departamento es obligatorio."
		if not municipio:
			errores["municipio"] = "El municipio es obligatorio."

		if errores:
			return render(request, "tiendas/update_shop.html", {
				"shop": shop,
				"errores": errores,
				"valores": valores,
			})

		request.session["update_shop_step1"] = valores
		return redirect("tiendas:update_shop_step2")

	return render(request, "tiendas/update_shop.html", {
		"shop": shop,
		"errores": errores,
		"valores": valores,
	})


@never_cache
def update_shop_step2(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	shop = Shop.objects.filter(owner=request.user).order_by("-created_at").first()
	if not shop:
		return redirect("tiendas:create_shop_step1")

	step1 = request.session.get("update_shop_step1", {})
	if not step1:
		step1 = {
			"nombre": shop.nombre or "",
			"telefono": shop.telefono or "",
			"email": shop.email or "",
			"departamento": shop.departamento or "",
			"municipio": shop.municipio or "",
		}

	errores = {}
	valores = {
		"tiene_punto_fisico": "si" if shop.punto_fisico else "no",
		"horario": shop.horario or "",
		"url": "",
		"direccion": shop.direccion or "",
		"descripcion": shop.descripcion or "",
	}

	if request.method == "POST":
		tiene_punto_fisico = request.POST.get("tiene_punto_fisico", "si").strip()
		usa_punto_fisico = tiene_punto_fisico == "si"
		horario = request.POST.get("horario", "").strip()
		direccion = request.POST.get("direccion", "").strip()
		descripcion = request.POST.get("descripcion", "").strip()
		url = request.POST.get("url", "").strip()

		valores = {
			"tiene_punto_fisico": tiene_punto_fisico,
			"horario": horario,
			"url": url,
			"direccion": direccion,
			"descripcion": descripcion,
		}

		if usa_punto_fisico:
			if not horario:
				errores["horario"] = "El horario es obligatorio si tienes punto fisico."
			if not direccion:
				errores["direccion"] = "La direccion es obligatoria si tienes punto fisico."
		else:
			horario = "No aplica"
			direccion = None

		if errores:
			return render(request, "tiendas/update_shop2.html", {
				"shop": shop,
				"errores": errores,
				"valores": valores,
			})

		shop.nombre = step1.get("nombre", shop.nombre)
		shop.telefono = step1.get("telefono", shop.telefono)
		shop.email = step1.get("email", shop.email)
		shop.departamento = step1.get("departamento", shop.departamento)
		shop.municipio = step1.get("municipio", shop.municipio)
		shop.punto_fisico = usa_punto_fisico
		shop.horario = horario
		shop.direccion = direccion
		shop.descripcion = descripcion
		shop.save()

		request.session.pop("update_shop_step1", None)
		return redirect("tiendas:profile_shop")

	return render(request, "tiendas/update_shop2.html", {
		"shop": shop,
		"errores": errores,
		"valores": valores,
	})
