from django.db import models

# Create your models here.
class Register(models.Model):
    id_envio = models.IntegerField()
    direccion_destino = models.CharField(max_length = 255)
    estado_envio = models.CharField(max_length = 20)
    fecha_envio = models.DateField()
    fecha_entrega = models.DateField()

class Login(models.Model):
    id_transportista = models.IntegerField()
    nombre_transportista = models.CharField(max_length = 100)
    telefono = models.IntegerField()
    correo_electronico = models.CharField(max_length = 255)