from django.db import models

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
    descripcion_perfil = models.CharField(max_length=100, null=True, blank=True)
    contrasena = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, default="activo")
    
    # Campos para reset de contraseña
    codigo_reset = models.CharField(max_length=6, null=True, blank=True)
    fecha_expiracion_codigo = models.DateTimeField(null=True, blank=True)

    # Campo para persistir validación de código admin
    admin_code_validated = models.BooleanField(default=False)

    # Seguridad de inicio de sesion
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.numero_documento}"
