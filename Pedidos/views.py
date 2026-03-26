"""
Vistas del modulo de pedidos.

Responsabilidades principales:
- Listar pedidos para cliente y agricultor.
- Confirmar pedidos automaticamente cuando expira la ventana de cancelacion.
- Permitir cambios de estado del pedido por parte del agricultor.
- Gestionar cancelacion por parte del cliente dentro de la ventana permitida.
- Mostrar comprobante/detalle de pedidos.

Nota de negocio:
La confirmacion automatica se basa en `Order.CANCEL_WINDOW_HOURS` para evitar
pedidos pendientes indefinidamente.
"""

from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from datetime import timedelta

# Confirmar pedido por el cliente
@require_POST
@never_cache
def confirm_order(request, order_id):
	"""Confirma manualmente un pedido pendiente del cliente autenticado.

	Solo aplica cuando el pedido pertenece al cliente y sigue en estado
	`pending`; en caso contrario no modifica el estado.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	order = get_object_or_404(Order, pk=order_id, customer=request.user)
	if order.status == Order.STATUS_PENDING:
		order.status = Order.STATUS_CONFIRMED
		order.save(update_fields=["status"])

	return redirect("pedidos:orders_client")

from django.db.models import Prefetch
from django.utils import timezone
from Tiendas.models import Shop
from .models import Order, OrderItem

# Create your views here.


@never_cache
def orders_client(request):
	"""Lista los pedidos del cliente y auto-confirma pendientes vencidos.

	Antes de renderizar, marca como confirmados los pedidos cuya ventana
	de cancelacion ya expiro.
	"""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	# Auto-confirm orders whose 7-hour cancellation window has expired
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
	"""Muestra los pedidos que contienen productos del agricultor actual.

	Tambien ejecuta la confirmacion automatica para pedidos pendientes
	vencidos y precarga los items del agricultor en `my_items`.
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

	# Mostrar todos los pedidos donde el agricultor tenga productos (sin filtrar por cutoff)
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
	"""Renderiza el detalle de un pedido desde la perspectiva del agricultor.

	Si el agricultor no tiene items en el pedido, redirige al listado para
	evitar acceso a pedidos ajenos.
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
	"""Actualiza el estado de un pedido cuando el agricultor tiene items.

	Restringe los cambios a estados permitidos y evita modificar pedidos
	que ya fueron cancelados.
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
	"""Cancela un pedido del cliente dentro de la ventana permitida."""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	order = get_object_or_404(Order, pk=order_id, customer=request.user)
	if order.can_cancel:
		order.status = Order.STATUS_CANCELLED
		order.save(update_fields=["status"])

	return redirect("pedidos:orders_client")


@never_cache
def order_receipt(request, order_id):
	"""Genera la vista de comprobante para un pedido del cliente."""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	order = get_object_or_404(Order, pk=order_id, customer=request.user)
	items = order.items.select_related("product", "farmer").all()

	return render(request, "pedidos/comprobante.html", {
		"order": order,
		"items": items,
	})
