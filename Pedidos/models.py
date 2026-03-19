from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Order(models.Model):
	STATUS_PENDING = "pending"
	STATUS_CONFIRMED = "confirmed"
	STATUS_IN_PROGRESS = "in_progress"
	STATUS_COMPLETED = "completed"
	STATUS_CANCELLED = "cancelled"

	STATUS_CHOICES = [
		(STATUS_PENDING, "Pendiente"),
		(STATUS_CONFIRMED, "Confirmado"),
		(STATUS_IN_PROGRESS, "En curso"),
		(STATUS_COMPLETED, "Completado"),
		(STATUS_CANCELLED, "Cancelado"),
	]

	CANCEL_WINDOW_HOURS = 7

	customer = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="orders_as_customer",
	)
	total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
	payment_method = models.CharField(max_length=60, blank=True, default="")
	delivery_method = models.CharField(max_length=60, blank=True, default="")
	delivery_address = models.CharField(max_length=255, blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "pedidos_order"
		ordering = ["-created_at"]

	def __str__(self):
		return f"Pedido #{self.id} - {self.customer.username}"

	@property
	def cancel_deadline(self):
		return self.created_at + timedelta(hours=self.CANCEL_WINDOW_HOURS)

	@property
	def cancel_deadline_iso(self):
		return self.cancel_deadline.isoformat()

	@property
	def can_cancel(self):
		return self.status == self.STATUS_PENDING and timezone.now() < self.cancel_deadline


class OrderItem(models.Model):
	order = models.ForeignKey(
		Order,
		on_delete=models.CASCADE,
		related_name="items",
	)
	product = models.ForeignKey(
		"Productos.Product",
		on_delete=models.CASCADE,
		related_name="order_items",
	)
	farmer = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="order_items_as_farmer",
	)
	quantity = models.DecimalField(max_digits=10, decimal_places=2)
	subtotal = models.DecimalField(max_digits=12, decimal_places=2)

	class Meta:
		db_table = "pedidos_order_item"

	def __str__(self):
		return f"Item #{self.id} - {self.product.nombre}"
