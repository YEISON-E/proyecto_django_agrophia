from django.shortcuts import render
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from datetime import datetime

from .models import Shop
from Productos.models import Product


def user_has_shop(user):
	if not user or not user.is_authenticated:
		return False
	return Shop.objects.filter(owner=user).exists()


def resolve_legacy_tienda_route(page):
	legacy_routes = {
		"create-shop.html": ("redirect", "tiendas:create_farmer_perfil"),
		"create-farmer-perfil.html": ("redirect", "tiendas:create_farmer_perfil"),
		"create-shop2.html": ("redirect", "tiendas:create_shop_step2"),
		"interface_farmer.html": ("redirect", "tiendas:interface_farmer"),
		"form_subir_producto.html": ("redirect", "productos:create_product"),
		"form_subir_producto2.html": ("redirect", "productos:create_product2"),
	}
	return legacy_routes.get(page)


def create_farmer_perfil(request):
	return render(request, "tiendas/create-farmer-perfil.html")


@never_cache
def interface_farmer(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	productos = Product.objects.filter(owner=request.user).prefetch_related("images").order_by("-created_at")

	return render(request, "tiendas/interface_farmer.html", {
		"productos": productos,
	})


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

	if request.method == "POST":
		step1 = request.session.get("shop_step1")

		hora_apertura = request.POST.get("hora_apertura", "").strip()
		hora_cierre = request.POST.get("hora_cierre", "").strip()

		if not hora_apertura or not hora_cierre:
			return render(request, "tiendas/create-shop2.html", {
				"error_horario": "Debes ingresar la hora de apertura y cierre.",
			})

		try:
			apertura_dt = datetime.strptime(hora_apertura, "%H:%M")
			cierre_dt = datetime.strptime(hora_cierre, "%H:%M")
		except ValueError:
			return render(request, "tiendas/create-shop2.html", {
				"error_horario": "Formato de horario invalido.",
			})

		if cierre_dt <= apertura_dt:
			return render(request, "tiendas/create-shop2.html", {
				"error_horario": "La hora de cierre debe ser mayor que la de apertura.",
			})

		horario = f"{hora_apertura} - {hora_cierre}"

		Shop.objects.create(
			owner=request.user if request.user.is_authenticated else None,
			nombre=step1["nombre"],
			telefono=step1["telefono"],
			email=step1["email"],
			departamento=step1["departamento"],
			municipio=step1["municipio"],
			horario=horario,
			direccion=request.POST.get("direccion"),
			descripcion=request.POST.get("descripcion"),
		)

		del request.session["shop_step1"]

		request.session["shop_success"] = True
		return redirect("tiendas:create_shop_step2")

	return render(request, "tiendas/create-shop2.html", {"shop_success": shop_success})
