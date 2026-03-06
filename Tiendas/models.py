from django.db import models
from django.contrib.auth.models import User


class Shop(models.Model):
	owner = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="shops",
		null=True,
		blank=True,
	)

	nombre = models.CharField(max_length=100)
	telefono = models.CharField(max_length=15)
	email = models.EmailField()

	departamento = models.CharField(max_length=50)
	municipio = models.CharField(max_length=50)
	punto_fisico = models.BooleanField(default=True)
	is_active = models.BooleanField(default=True)

	horario = models.CharField(max_length=100)
	direccion = models.CharField(max_length=255, blank=True, null=True)
	descripcion = models.TextField(blank=True, null=True)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "usuarios_shop"

	def __str__(self):
		return self.nombre
