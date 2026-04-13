"""
Vistas del modulo de carrito de compras.

Cobertura funcional:
- Visualizacion del carrito con saneamiento de productos no validos.
- Agregar, eliminar y actualizar cantidades de productos.
- Validaciones de stock en tiempo real y durante checkout.
- Generacion de pedido y detalle de items en transaccion atomica.
- Descuento de inventario con bloqueo de filas para evitar sobreventa.

Aseguramiento de consistencia:
El checkout usa `transaction.atomic()` y `select_for_update()` para confirmar
existencias finales justo antes de crear el pedido.
"""

from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
# Importación de dependencias necesarias para ejecutar esta vista.
from django.views.decorators.http import require_POST
from django.db import transaction

from Productos.models import Product
from Pedidos.models import Order, OrderItem
from usuarios.models import Register

# Create your views here.


@never_cache
def shopping_cart(request):
	"""Renderiza el carrito del usuario saneando items invalidos.

	Durante el render:
	- Elimina productos inexistentes/inactivos.
	- Ajusta cantidades al stock real.
	- Calcula subtotal y total final.
	"""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	cart = request.session.get("shopping_cart", {})
	product_ids = []
	for product_id in cart.keys():
		try:
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			product_ids.append(int(product_id))
		except (TypeError, ValueError):
			continue

	products = Product.objects.filter(
		id__in=product_ids,
		is_active=True,
		shop__is_active=True,
	# Paso de apoyo dentro del flujo principal de la funcionalidad.
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
		# Control de flujo y validación de condiciones del proceso.
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
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"product": product,
			"quantity": quantity,
			"subtotal": subtotal,
			"image_url": image_url,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
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
	# Control de flujo y validación de condiciones del proceso.
	except Register.DoesNotExist:
		pass

	return render(request, "carrito_compras/shopping-car.html", {
		"cart_items": cart_items,
		"cart_total": total,
		"user_address": user_address,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"can_pickup_in_store": can_pickup_in_store,
		"cart_notice": cart_notice,
	})


@require_POST
def add_to_cart(request):
	"""Agrega un producto activo al carrito validando cantidad y stock."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
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
		# Retorno de respuesta según el estado y resultado de la operación.
		return JsonResponse({"ok": False, "message": "Cantidad inválida."}, status=400)

	if quantity <= 0:
		return JsonResponse({"ok": False, "message": "Cantidad inválida."}, status=400)

	if product.stock <= 0:
		return JsonResponse({"ok": False, "message": "Este producto no tiene stock disponible."}, status=400)

	if quantity > product.stock:
		return JsonResponse({
			"ok": False,
			"message": f"Solo hay {product.stock} unidades disponibles para este producto.",
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		}, status=400)

	cart = request.session.get("shopping_cart", {})
	product_key = str(product.id)
	if product_key in cart:
		items_count = len(cart)
		# Retorno de respuesta según el estado y resultado de la operación.
		return JsonResponse({
			"ok": True,
			"already_in_cart": True,
			"message": "Este producto ya esta en el carrito.",
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
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
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"items_count": items_count,
	})


@require_POST
def remove_from_cart(request, product_id):
	"""Quita un producto del carrito por su ID."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	cart = request.session.get("shopping_cart", {})
	cart.pop(str(product_id), None)

	request.session["shopping_cart"] = cart
	request.session.modified = True

	return redirect("carrito_compras:shopping_cart")


@require_POST
def update_cart_quantity(request, product_id):
	"""Actualiza la cantidad de un item respetando disponibilidad."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "No autenticado."}, status=401)
		return redirect("usuarios:login")

	cart = request.session.get("shopping_cart", {})
	if str(product_id) not in cart:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Producto no encontrado en el carrito."}, status=404)
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect("carrito_compras:shopping_cart")

	quantity_value = (request.POST.get(f"quantity_{product_id}") or "").strip()
	try:
		quantity = int(quantity_value)
	except (TypeError, ValueError):
		# Control de flujo y validación de condiciones del proceso.
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Cantidad inválida."}, status=400)
		return redirect("carrito_compras:shopping_cart")

	try:
		product = Product.objects.get(pk=product_id, is_active=True, shop__is_active=True)
	except Product.DoesNotExist:
		cart.pop(str(product_id), None)
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		request.session["shopping_cart"] = cart
		request.session.modified = True
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Producto no disponible actualmente."}, status=400)
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect("carrito_compras:shopping_cart")

	quantity = max(1, quantity)
	if product.stock <= 0:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({"ok": False, "message": "Este producto no tiene stock disponible."}, status=400)
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect("carrito_compras:shopping_cart")

	if quantity > product.stock:
		if request.headers.get("X-Requested-With") == "XMLHttpRequest":
			return JsonResponse({
				"ok": False,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
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
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"quantity": cart[str(product_id)],
		})

	return redirect("carrito_compras:shopping_cart")


@require_POST
@never_cache
def checkout(request):
	"""Convierte el carrito en pedido usando validacion final de inventario.

	La operacion se ejecuta en una transaccion para prevenir inconsistencias
	y descuenta stock de cada producto confirmado.
	"""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	# 1) Verifica precondiciones basicas del checkout.
	cart = request.session.get("shopping_cart", {})
	if not cart:
		return redirect("carrito_compras:shopping_cart")

	payment_method = (request.POST.get("payment_method") or "").strip()
	delivery_method = (request.POST.get("delivery_method") or "").strip()
	delivery_address = (request.POST.get("delivery_address") or "").strip()
	valid_payment_methods = {"Tarjeta", "Nequi"}
	# Actualización de estado intermedio que será utilizada en pasos posteriores.
	valid_delivery_methods = {"Recogido en tienda", "Envío a domicilio"}

	if payment_method not in valid_payment_methods or delivery_method not in valid_delivery_methods:
		return redirect("carrito_compras:shopping_cart")

	# 2) Carga productos vigentes y valida reglas de entrega.
	# Se inicializa una lista vacia para guardar IDs de producto en formato entero.
	# En la sesion, las claves del carrito suelen venir como texto, por eso se normalizan.
	product_ids = []
	# Se recorren todas las claves del carrito (cada clave representa un product_id).
	for product_id in cart.keys():
		try:
			# Conversion segura a entero para usar el ID en consultas SQL.
			# Si la conversion falla, ese item se considera invalido y no se procesa.
			product_ids.append(int(product_id))
		except (TypeError, ValueError):
			# Se ignoran IDs dañados (ej: vacios, texto no numerico o tipos inesperados)
			# para proteger el checkout contra datos corruptos en sesion.
			continue

	# Se consultan solo productos que siguen siendo comprables:
	# - id incluido en el carrito actual
	# - producto activo
	# - tienda activa
	products = Product.objects.filter(
		id__in=product_ids,
		is_active=True,
		shop__is_active=True,
	# Paso de apoyo dentro del flujo principal de la funcionalidad.
	).select_related("owner", "shop")
	# Se crea un diccionario {id: producto} para busquedas O(1) durante validaciones.
	# Esto evita recorrer toda la lista cada vez que se necesita un producto puntual.
	products_by_id = {product.id: product for product in products}
	# Esta bandera valida si TODOS los productos del carrito permiten recogida en tienda.
	# Solo sera True cuando cada producto tenga tienda asociada y esa tienda tenga
	# habilitado punto_fisico.
	can_pickup_in_store = all(
		product.shop and product.shop.punto_fisico
		for product in products_by_id.values()
	)

	# Regla de negocio: si el usuario eligio "Recogido en tienda" pero alguno de los
	# productos no cumple esa modalidad, se cancela checkout y se devuelve al carrito.
	if delivery_method == "Recogido en tienda" and not can_pickup_in_store:
		return redirect("carrito_compras:shopping_cart")

	# Si NO es envio a domicilio, la direccion no aplica y se limpia para evitar
	# guardar informacion inconsistente en el pedido.
	if delivery_method != "Envío a domicilio":
		delivery_address = ""
	# Si SI es envio a domicilio, la direccion es obligatoria.
	# Si viene vacia, se interrumpe el flujo y se regresa al carrito.
	elif not delivery_address:
		return redirect("carrito_compras:shopping_cart")

	# 3) Recalcula montos y valida stock antes de bloquear filas.
	total_amount = 0
	items_data = []
	for product_id_str, quantity_value in cart.items():
		try:
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
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
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			"quantity": quantity,
			"subtotal": subtotal,
		})

	if not items_data:
		return redirect("carrito_compras:shopping_cart")

	# 4) Confirma inventario bajo bloqueo transaccional y crea pedido/items.
	with transaction.atomic():
		# Se bloquean en BD (FOR UPDATE) las filas de productos involucradas.
		# Esto evita condiciones de carrera cuando dos usuarios compran el mismo
		# producto al mismo tiempo, porque nadie mas puede descontar stock hasta
		# que esta transaccion termine.
		locked_products = Product.objects.select_for_update().filter(id__in=[item["product"].id for item in items_data])
		# Mapa rapido por ID para consultar cada producto bloqueado en O(1).
		# Se usa en las validaciones finales y al momento de descontar inventario.
		locked_map = {product.id: product for product in locked_products}

		# Revalidacion FINAL con datos bloqueados: aqui se confirma que nada
		# cambio entre la primera validacion y este punto critico del checkout.
		for item in items_data:
			locked_product = locked_map.get(item["product"].id)
			# Si el producto desaparecio del lock, se desactivo o se agoto,
			# se cancela el checkout para no crear un pedido inconsistente.
			if not locked_product or not locked_product.is_active or locked_product.stock <= 0:
				request.session["cart_notice"] = f"{item['product'].nombre} ya no está disponible."
				return redirect("carrito_compras:shopping_cart")
			# Si la cantidad solicitada ya supera el stock real bloqueado,
			# tambien se cancela para impedir sobreventa.
			if item["quantity"] > locked_product.stock:
				request.session["cart_notice"] = (
					f"No hay stock suficiente para {locked_product.nombre}. Disponible: {locked_product.stock}."
				)
				# Retorno de respuesta según el estado y resultado de la operación.
				return redirect("carrito_compras:shopping_cart")

		# Cuando todo es valido, se crea la cabecera del pedido con el total,
		# metodos seleccionados y estado inicial pendiente.
		order = Order.objects.create(
			customer=request.user,
			total_amount=total_amount,
			payment_method=payment_method,
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			delivery_method=delivery_method,
			delivery_address=delivery_address,
			status=Order.STATUS_PENDING,
		)

		# Se insertan todos los items del pedido en lote (bulk_create),
		# reduciendo roundtrips a BD y manteniendo eficiencia.
		OrderItem.objects.bulk_create([
			OrderItem(
				order=order,
				product=item["product"],
				# Actualización de estado intermedio que será utilizada en pasos posteriores.
				farmer=item["product"].owner,
				quantity=item["quantity"],
				subtotal=item["subtotal"],
			)
			# Iteración sobre datos para aplicar reglas de negocio paso a paso.
			for item in items_data
		])

		# 5) Descuenta inventario y desactiva productos agotados.
		for item in items_data:
			locked_product = locked_map[item["product"].id]
			locked_product.stock -= item["quantity"]
			if locked_product.stock <= 0:
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				locked_product.stock = 0
				locked_product.is_active = False
				locked_product.save(update_fields=["stock", "is_active"])
			else:
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				locked_product.save(update_fields=["stock"])

	# 6) Limpia carrito en sesion y redirige a pedidos del cliente.
	request.session["shopping_cart"] = {}
	request.session.modified = True

	return redirect("pedidos:orders_client")
