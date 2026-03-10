from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

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

	for product_id_str, quantity_value in cart.items():
		try:
			product_id = int(product_id_str)
			quantity = max(1, int(quantity_value))
		except (TypeError, ValueError):
			continue

		product = products_by_id.get(product_id)
		if not product:
			continue

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

	cart = request.session.get("shopping_cart", {})
	current_qty = int(cart.get(str(product.id), 0))
	cart[str(product.id)] = current_qty + quantity

	request.session["shopping_cart"] = cart
	request.session.modified = True

	items_count = sum(int(quantity) for quantity in cart.values())

	return JsonResponse({
		"ok": True,
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

	cart[str(product_id)] = max(1, quantity)
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

		subtotal = product.precio * quantity
		total_amount += subtotal
		items_data.append({
			"product": product,
			"quantity": quantity,
			"subtotal": subtotal,
		})

	if not items_data:
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

	request.session["shopping_cart"] = {}
	request.session.modified = True

	return redirect("pedidos:orders_client")
