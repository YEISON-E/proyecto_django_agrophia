from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Product(models.Model):
	TIPO_FRUTAS = "Frutas"
	TIPO_VEGETALES = "Vegetales"
	TIPO_LACTEOS = "Lácteos"
	TIPO_CARNE = "Carne"
	TIPO_GRANOS = "Granos"
	TIPO_OTROS = "Otros"

	TIPO_CHOICES = [
		(TIPO_FRUTAS, "Frutas"),
		(TIPO_VEGETALES, "Vegetales"),
		(TIPO_LACTEOS, "Lácteos"),
		(TIPO_CARNE, "Carne"),
		(TIPO_GRANOS, "Granos"),
		(TIPO_OTROS, "Otros"),
	]

	UNIDAD_LIBRA = "Libra"
	UNIDAD_KILO = "Kilo"
	UNIDAD_ARROBA = "Arroba"
	UNIDAD_LITRO = "Litro"

	UNIDAD_CHOICES = [
		(UNIDAD_LIBRA, "Libra"),
		(UNIDAD_KILO, "Kilo"),
		(UNIDAD_ARROBA, "Arroba"),
		(UNIDAD_LITRO, "Litro"),
	]

	METODO_PAGO_CONTADO = "contado"
	METODO_PAGO_ENTREGA = "entrega"
	METODO_PAGO_TRANSFERENCIA = "transferencia"

	METODO_PAGO_CHOICES = [
		(METODO_PAGO_CONTADO, "Pago de contado"),
		(METODO_PAGO_ENTREGA, "Pago contra entrega"),
		(METODO_PAGO_TRANSFERENCIA, "Transferencia"),
	]

	METODO_ENTREGA_DOMICILIO = "domicilio"
	METODO_ENTREGA_TIENDA = "tienda"
	METODO_ENTREGA_CITA = "cita"

	METODO_ENTREGA_CHOICES = [
		(METODO_ENTREGA_DOMICILIO, "Envío a domicilio"),
		(METODO_ENTREGA_TIENDA, "Recogido en tienda"),
		(METODO_ENTREGA_CITA, "Entrega bajo cita"),
	]

	UNIDADES_POR_TIPO = {
		TIPO_FRUTAS: {UNIDAD_LIBRA, UNIDAD_KILO, UNIDAD_ARROBA},
		TIPO_VEGETALES: {UNIDAD_LIBRA, UNIDAD_KILO, UNIDAD_ARROBA},
		TIPO_LACTEOS: {UNIDAD_LITRO},
		TIPO_CARNE: {UNIDAD_LIBRA, UNIDAD_KILO, UNIDAD_ARROBA},
		TIPO_GRANOS: {UNIDAD_LIBRA, UNIDAD_KILO, UNIDAD_ARROBA},
		TIPO_OTROS: {UNIDAD_LIBRA, UNIDAD_KILO, UNIDAD_ARROBA, UNIDAD_LITRO},
	}

	owner = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name="products",
	)
	shop = models.ForeignKey(
		"Tiendas.Shop",
		on_delete=models.CASCADE,
		related_name="products",
		null=True,
		blank=True,
	)

	nombre = models.CharField(max_length=120)
	tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
	tipo_otro = models.CharField(max_length=60, blank=True)
	unidad = models.CharField(max_length=10, choices=UNIDAD_CHOICES)

	precio = models.DecimalField(max_digits=12, decimal_places=2)
	descripcion = models.TextField()
	garantia = models.CharField(max_length=120)
	metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
	metodo_entrega = models.CharField(max_length=20, choices=METODO_ENTREGA_CHOICES)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "productos_product"

	def clean(self):
		errors = {}

		if self.tipo == self.TIPO_OTROS:
			if not (self.tipo_otro or "").strip():
				errors["tipo_otro"] = "Debes especificar el tipo de producto."
		else:
			self.tipo_otro = ""

		unidades_permitidas = self.UNIDADES_POR_TIPO.get(self.tipo, set())
		if self.unidad and self.unidad not in unidades_permitidas:
			errors["unidad"] = f"La unidad no aplica para {self.tipo}."

		if self.precio is not None and self.precio <= 0:
			errors["precio"] = "El precio debe ser mayor que 0."

		if (self.nombre or "").strip() and len(self.nombre.strip()) < 3:
			errors["nombre"] = "El nombre debe tener al menos 3 caracteres."

		if (self.descripcion or "").strip() and len(self.descripcion.strip()) < 10:
			errors["descripcion"] = "La descripción debe tener al menos 10 caracteres."

		if (self.garantia or "").strip() and len(self.garantia.strip()) < 3:
			errors["garantia"] = "La garantía debe tener al menos 3 caracteres."

		if errors:
			raise ValidationError(errors)

	def __str__(self):
		return self.nombre


class ProductImage(models.Model):
	product = models.ForeignKey(
		Product,
		on_delete=models.CASCADE,
		related_name="images",
	)
	image = models.ImageField(upload_to="productos/")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = "productos_product_image"

	def __str__(self):
		return f"Imagen de {self.product.nombre}"
