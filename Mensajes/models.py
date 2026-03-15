from django.db import models
from django.contrib.auth.models import User

from Productos.models import Product
from usuarios.models import Register

# Create your models here.


class CustomerMessage(models.Model):
	STATUS_PENDING = "pending"
	STATUS_REPLIED = "replied"
	STATUS_REJECTED = "rejected"

	STATUS_CHOICES = [
		(STATUS_PENDING, "Sin respuesta"),
		(STATUS_REPLIED, "Respondido"),
		(STATUS_REJECTED, "Rechazado"),
	]

	sender = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="messages_sent",
	)
	receiver = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="messages_received",
	)
	product = models.ForeignKey(
		Product,
		on_delete=models.CASCADE,
		related_name="messages",
	)

	content = models.TextField()
	reply_content = models.TextField(blank=True)
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)

	created_at = models.DateTimeField(auto_now_add=True)
	replied_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		db_table = "mensajes_customer_message"
		ordering = ["-created_at"]

	def __str__(self):
		return f"Mensaje #{self.id} de {self.sender_id} a {self.receiver_id}"


class FarmerReply(models.Model):
	message = models.ForeignKey(
		CustomerMessage,
		on_delete=models.CASCADE,
		related_name="farmer_replies",
	)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "mensajes_farmer_reply"
		ordering = ["created_at"]

	def __str__(self):
		return f"Respuesta #{self.id} al mensaje #{self.message_id}"


class AdminToUserMessage(models.Model):
    usuario = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='mensajes_admin')
    texto = models.TextField()
    enviado = models.BooleanField(default=False)
    leido = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje admin para {self.usuario} - {self.creado:%Y-%m-%d %H:%M}"
