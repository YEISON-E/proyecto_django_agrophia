from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Register(models.Model):
    id_usuario = models.IntegerField()
    foto = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    tipo_documento = models.CharField(max_length=50)
    numero_documento = models.CharField(max_length=30, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo_electronico = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, unique=True)
    departamento = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    direccion_completa = models.CharField(max_length=255)
    descripcion_perfil = models.CharField(max_length=40, null=True, blank=True)
    contrasena = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, default="activo")
    
    # Campos para reset de contraseña
    codigo_reset = models.CharField(max_length=6, null=True, blank=True)
    fecha_expiracion_codigo = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.numero_documento}"

class Shop(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shops",
        null=True,
        blank=True
    )

    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    email = models.EmailField()

    departamento = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)

    horario = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre