from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from Productos.models import Product

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
	).prefetch_related("images")
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

	return render(request, "carrito_compras/shopping-car.html", {
		"cart_items": cart_items,
		"cart_total": total,
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
