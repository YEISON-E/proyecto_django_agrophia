from django.db import models

# Create your models here.
class Register(models.Model):
    id_usuario = models.IntegerField()
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    tipo_documento = models.CharField(max_length=50)
    numero_documento = models.CharField(max_length=30)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo_electronico = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    departamento = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    direccion_completa = models.CharField(max_length=255)
    descripcion_perfil = models.CharField(max_length=40, null=True, blank=True)
    contrasena = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, default="activo")

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.numero_documento}"

class Login(models.Model):
    id_transportista = models.IntegerField()
    nombre_transportista = models.CharField(max_length = 100)
    telefono = models.IntegerField()
    correo_electronico = models.CharField(max_length = 255)