from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.db import transaction

from Productos.models import Product
from Pedidos.models import Order, OrderItem
from usuarios.models import Register

# Create your views here.


@never_cache
def shopping_cart(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	cart = request.session.get("shopping_cart", {})
	product_ids = []
	for product_id in cart.keys():
		try:
			product_ids.append(int(product_id))
		except (TypeError, ValueError):
			continue

	products = Product.objects.filter(
		id__in=product_ids,
		is_active=True,
		shop__is_active=True,
	).select_related("shop").prefetch_related("images")
	products_by_id = {product.id: product for product in products}

	cart_items = []
	total = 0
	clean_cart = {}
	notice_messages = []

	for product_id_str, quantity_value in cart.items():
		try:
			product_id = int(product_id_str)
			quantity = max(1, int(quantity_value))
		except (TypeError, ValueError):
			continue

		product = products_by_id.get(product_id)
		if not product:
			notice_messages.append("Se eliminaron productos no disponibles del carrito.")
			continue

		if product.stock <= 0:
			notice_messages.append(f"{product.nombre} ya no tiene stock disponible y fue retirado del carrito.")
			continue

		if quantity > product.stock:
			quantity = product.stock
			notice_messages.append(f"La cantidad de {product.nombre} fue ajustada al stock disponible ({product.stock}).")

		product_images = list(product.images.all())
		first_image = product_images[0] if product_images else None
		image_url = first_image.image.url if first_image and first_image.image else ""

		subtotal = product.precio * quantity
		total += subtotal
		clean_cart[str(product_id)] = quantity
		cart_items.append({
			"product": product,
			"quantity": quantity,
			"subtotal": subtotal,
			"image_url": image_url,
		})

	request.session["shopping_cart"] = clean_cart
	request.session.modified = True

	cart_notice = request.session.pop("cart_notice", "")
	if notice_messages:
		combined_notice = " ".join(dict.fromkeys(notice_messages))
		cart_notice = f"{cart_notice} {combined_notice}".strip()

	can_pickup_in_store = bool(cart_items) and all(
		item["product"].shop and item["product"].shop.punto_fisico
		for item in cart_items
	)

	user_address = ""
	try:
		profile = Register.objects.get(id_usuario=request.user.id)
		user_address = profile.direccion_completa or ""
	except Register.DoesNotExist:
		pass

	return render(request, "carrito_compras/shopping-car.html", {
		"cart_items": cart_items,
		"cart_total": total,
		"user_address": user_address,
		"can_pickup_in_store": can_pickup_in_store,
		"cart_notice": cart_notice,
	})


@require_POST
def add_to_cart(request):
	if not request.user.is_authenticated:
		return JsonResponse({"ok": False, "message": "No autenticado."}, status=401)

	product_id = (request.POST.get("product_id") or "").strip()
	if not product_id:
		return JsonResponse({"ok": False, "message": "Producto inválido."}, status=400)

	try:
		product = Product.objects.get(pk=int(product_id), is_active=True, shop__is_active=True)
	except (ValueError, Product.DoesNotExist):
		return JsonResponse({"ok": False, "message": "Producto no encontrado."}, status=404)

	quantity_value = (request.POST.get("quantity") or "").strip()
	try:
		quantity = int(quantity_value)
	except (TypeError, ValueError):
		return JsonResponse({"ok": False, "message": "Cantidad inválida."}, status=400)

	if quantity <= 0:
		return JsonResponse({"ok": False, "message": "Cantidad inválida."}, status=400)

	if product.stock <= 0:
		return JsonResponse({"ok": False, "message": "Este producto no tiene stock disponible."}, status=400)

	if quantity > product.stock:
		return JsonResponse({
			"ok": False,
			"message": f"Solo hay {product.stock} unidades disponibles para este producto.",
		}, status=400)

	cart = request.session.get("shopping_cart", {})
	product_key = str(product.id)
	if product_key in cart:
		items_count = len(cart)
		return JsonResponse({
			"ok": True,
			"already_in_cart": True,
			"message": "Este producto ya esta en el carrito.",
			"items_count": items_count,
		})

	cart[product_key] = quantity

	request.session["shopping_cart"] = cart
	request.session.modified = True

	items_count = len(cart)

	return JsonResponse({
		"ok": True,
		"already_in_cart": False,
		"message": "Producto agregado al carrito.",
		"items_count": items_count,
	})


@require_POST
def remove_from_cart(request, product_id):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	cart = request.session.get("shopping_cart", {})
	cart.pop(str(product_id), None)

	request.session["shopping_cart"] = cart
	request.session.modified = True

	return redirect("carrito_compras:shopping_cart")


@require_POST
def update_cart_quantity(request, product_id):
	if not request.user.is_authenticated:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "No autenticado."}, status=401)
		return redirect("usuarios:login")

	cart = request.session.get("shopping_cart", {})
	if str(product_id) not in cart:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Producto no encontrado en el carrito."}, status=404)
		return redirect("carrito_compras:shopping_cart")

	quantity_value = (request.POST.get(f"quantity_{product_id}") or "").strip()
	try:
		quantity = int(quantity_value)
	except (TypeError, ValueError):
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Cantidad inválida."}, status=400)
		return redirect("carrito_compras:shopping_cart")

	try:
		product = Product.objects.get(pk=product_id, is_active=True, shop__is_active=True)
	except Product.DoesNotExist:
		cart.pop(str(product_id), None)
		request.session["shopping_cart"] = cart
		request.session.modified = True
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Producto no disponible actualmente."}, status=400)
		return redirect("carrito_compras:shopping_cart")

	quantity = max(1, quantity)
	if product.stock <= 0:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Este producto no tiene stock disponible."}, status=400)
		return redirect("carrito_compras:shopping_cart")

	if quantity > product.stock:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({
				"ok": False,
				"message": f"Solo hay {product.stock} unidades disponibles para este producto.",
			}, status=400)
		quantity = product.stock

	cart[str(product_id)] = quantity
	request.session["shopping_cart"] = cart
	request.session.modified = True

	if request.headers.get("X-Requested-With") == "XMLHttpRequest":
		return JsonResponse({
			"ok": True,
			"message": "Cantidad actualizada.",
			"quantity": cart[str(product_id)],
		})

	return redirect("carrito_compras:shopping_cart")


@require_POST
@never_cache
def checkout(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	cart = request.session.get("shopping_cart", {})
	if not cart:
		return redirect("carrito_compras:shopping_cart")

	payment_method = (request.POST.get("payment_method") or "").strip()
	delivery_method = (request.POST.get("delivery_method") or "").strip()
	delivery_address = (request.POST.get("delivery_address") or "").strip()
	valid_payment_methods = {"Tarjeta", "Nequi"}
	valid_delivery_methods = {"Recogido en tienda", "Envío a domicilio"}

	if payment_method not in valid_payment_methods or delivery_method not in valid_delivery_methods:
		return redirect("carrito_compras:shopping_cart")

	product_ids = []
	for product_id in cart.keys():
		try:
			product_ids.append(int(product_id))
		except (TypeError, ValueError):
			continue

	products = Product.objects.filter(
		id__in=product_ids,
		is_active=True,
		shop__is_active=True,
	).select_related("owner", "shop")
	products_by_id = {product.id: product for product in products}
	can_pickup_in_store = all(
		product.shop and product.shop.punto_fisico
		for product in products_by_id.values()
	)

	if delivery_method == "Recogido en tienda" and not can_pickup_in_store:
		return redirect("carrito_compras:shopping_cart")

	if delivery_method != "Envío a domicilio":
		delivery_address = ""
	elif not delivery_address:
		return redirect("carrito_compras:shopping_cart")

	total_amount = 0
	items_data = []
	for product_id_str, quantity_value in cart.items():
		try:
			product_id = int(product_id_str)
			quantity = max(1, int(quantity_value))
		except (TypeError, ValueError):
			continue

		product = products_by_id.get(product_id)
		if not product:
			continue

		if product.stock <= 0:
			request.session["cart_notice"] = f"{product.nombre} ya no tiene stock disponible."
			return redirect("carrito_compras:shopping_cart")

		if quantity > product.stock:
			request.session["cart_notice"] = f"Solo hay {product.stock} unidades disponibles para {product.nombre}."
			return redirect("carrito_compras:shopping_cart")

		subtotal = product.precio * quantity
		total_amount += subtotal
		items_data.append({
			"product": product,
			"quantity": quantity,
			"subtotal": subtotal,
		})

	if not items_data:
		return redirect("carrito_compras:shopping_cart")

	with transaction.atomic():
		locked_products = Product.objects.select_for_update().filter(id__in=[item["product"].id for item in items_data])
		locked_map = {product.id: product for product in locked_products}

		for item in items_data:
			locked_product = locked_map.get(item["product"].id)
			if not locked_product or not locked_product.is_active or locked_product.stock <= 0:
				request.session["cart_notice"] = f"{item['product'].nombre} ya no está disponible."
				return redirect("carrito_compras:shopping_cart")
			if item["quantity"] > locked_product.stock:
				request.session["cart_notice"] = (
					f"No hay stock suficiente para {locked_product.nombre}. Disponible: {locked_product.stock}."
				)
				return redirect("carrito_compras:shopping_cart")

		order = Order.objects.create(
			customer=request.user,
			total_amount=total_amount,
			payment_method=payment_method,
			delivery_method=delivery_method,
			delivery_address=delivery_address,
			status=Order.STATUS_PENDING,
		)

		OrderItem.objects.bulk_create([
			OrderItem(
				order=order,
				product=item["product"],
				farmer=item["product"].owner,
				quantity=item["quantity"],
				subtotal=item["subtotal"],
			)
			for item in items_data
		])

		for item in items_data:
			locked_product = locked_map[item["product"].id]
			locked_product.stock -= item["quantity"]
			if locked_product.stock <= 0:
				locked_product.stock = 0
				locked_product.is_active = False
				locked_product.save(update_fields=["stock", "is_active"])
			else:
				locked_product.save(update_fields=["stock"])

	request.session["shopping_cart"] = {}
	request.session.modified = True

	return redirect("pedidos:orders_client")
