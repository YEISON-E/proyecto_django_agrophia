"""Vistas del módulo de pedidos.

Resumen de negocio:
- El cliente puede confirmar o cancelar pedidos pendientes.
- El agricultor puede consultar pedidos con sus productos y cambiar estado.
- Los pedidos pendientes se confirman automáticamente al vencer la ventana de
  cancelación definida en ``Order.CANCEL_WINDOW_HOURS``.
"""

from datetime import timedelta

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from Tiendas.models import Shop
from .models import Order, OrderItem


@require_POST
@never_cache
def confirm_order(request, order_id):
	"""Confirma manualmente un pedido del cliente autenticado.

	Reglas:
	- Solo se permite para el propietario del pedido.
	- Solo cambia estado cuando el pedido está en ``pending``.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	order = get_object_or_404(Order, pk=order_id, customer=request.user)
	if order.status == Order.STATUS_PENDING:
		order.status = Order.STATUS_CONFIRMED
		order.save(update_fields=["status"])

	return redirect("pedidos:orders_client")


@never_cache
def orders_client(request):
	"""Lista pedidos del cliente y aplica confirmación automática de vencidos.

	Antes de renderizar, actualiza a ``confirmed`` los pedidos pendientes cuya
	fecha de creación supera la ventana de cancelación.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	# Confirma pendientes del cliente cuando vence la ventana de cancelación.
	cutoff = timezone.now() - timedelta(hours=Order.CANCEL_WINDOW_HOURS)
	Order.objects.filter(
		customer=request.user,
		status=Order.STATUS_PENDING,
		created_at__lt=cutoff,
	).update(status=Order.STATUS_CONFIRMED)

	orders = Order.objects.filter(customer=request.user).prefetch_related(
		Prefetch("items", queryset=OrderItem.objects.select_related("product", "farmer"))
	)

	return render(request, "pedidos/orders_client.html", {
		"orders": orders,
	})


@never_cache
def orders_farmer(request):
	"""Lista pedidos donde el agricultor actual tiene ítems asociados.

	También aplica confirmación automática de pedidos pendientes vencidos.
	Cada pedido retorna los ítems del agricultor en ``my_items`` para simplificar
	la plantilla.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	if not Shop.objects.filter(owner=request.user, is_active=True).exists():
		return redirect("usuarios:home_customer")

	cutoff = timezone.now() - timedelta(hours=Order.CANCEL_WINDOW_HOURS)
	Order.objects.filter(
		status=Order.STATUS_PENDING,
		created_at__lt=cutoff,
	).update(status=Order.STATUS_CONFIRMED)

	# Incluye pedidos que contienen al menos un ítem del agricultor autenticado.
	orders = Order.objects.filter(
		items__farmer=request.user
	).distinct().prefetch_related(
		Prefetch(
			"items",
			queryset=OrderItem.objects.filter(farmer=request.user).select_related("product"),
			to_attr="my_items",
		)
	).select_related("customer")

	return render(request, "pedidos/orders_farmer.html", {
		"orders": orders,
	})


@never_cache
def order_farmer_detail(request, order_id):
	"""Muestra el detalle de un pedido para el agricultor autenticado.

	Si el pedido no contiene productos del agricultor, redirige al listado para
	evitar exposición de información de terceros.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	if not Shop.objects.filter(owner=request.user, is_active=True).exists():
		return redirect("usuarios:home_customer")

	order = get_object_or_404(Order.objects.select_related("customer"), pk=order_id)
	items = list(order.items.filter(farmer=request.user).select_related("product", "farmer"))
	if not items:
		return redirect("pedidos:orders_farmer")

	farmer_total = sum((item.subtotal for item in items), 0)

	return render(request, "pedidos/order_farmer_detail.html", {
		"order": order,
		"items": items,
		"farmer_total": farmer_total,
	})


@require_POST
@never_cache
def update_order_status(request, order_id):
	"""Actualiza estado de un pedido desde el panel de agricultor.

	Reglas:
	- Solo puede actualizar quien participa en el pedido (tiene ítems).
	- No se permiten cambios si ya está cancelado.
	- El nuevo estado debe estar dentro del conjunto permitido.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	order = get_object_or_404(Order, pk=order_id)
	if not order.items.filter(farmer=request.user).exists():
		return redirect("pedidos:orders_farmer")

	if order.status == Order.STATUS_CANCELLED:
		return redirect("pedidos:orders_farmer")

	new_status = (request.POST.get("status") or "").strip()
	valid_statuses = {Order.STATUS_CONFIRMED, Order.STATUS_IN_PROGRESS, Order.STATUS_COMPLETED, Order.STATUS_CANCELLED}

	if new_status in valid_statuses:
		order.status = new_status
		order.save(update_fields=["status"])

	return redirect("pedidos:orders_farmer")


@require_POST
@never_cache
def cancel_order(request, order_id):
	"""Cancela un pedido del cliente si aún está dentro de la ventana válida."""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	order = get_object_or_404(Order, pk=order_id, customer=request.user)
	if order.can_cancel:
		order.status = Order.STATUS_CANCELLED
		order.save(update_fields=["status"])

	return redirect("pedidos:orders_client")


@never_cache
def order_receipt(request, order_id):
	"""Renderiza el comprobante de un pedido confirmado para su cliente.

	Reglas:
	- El pedido debe pertenecer al usuario autenticado.
	- Solo se permite acceso cuando el estado es ``confirmed``.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	order = get_object_or_404(Order, pk=order_id, customer=request.user)
	if order.status != Order.STATUS_CONFIRMED:
		return redirect("pedidos:orders_client")

	items = order.items.select_related("product", "farmer").all()

	return render(request, "pedidos/comprobante.html", {
		"order": order,
		"items": items,
	})
