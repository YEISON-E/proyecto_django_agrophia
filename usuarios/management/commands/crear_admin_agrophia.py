from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from usuarios.models import Register


class Command(BaseCommand):
    help = "Crea o actualiza un administrador (User + Register) para el flujo de Agrophia."

    def add_arguments(self, parser):
        parser.add_argument("--documento", required=True, help="Numero de documento (solo digitos)")
        parser.add_argument("--email", required=True, help="Correo del administrador")
        parser.add_argument("--nombres", required=True, help="Nombres")
        parser.add_argument("--apellidos", required=True, help="Apellidos")
        parser.add_argument("--telefono", required=True, help="Telefono")
        parser.add_argument("--password", required=True, help="Contrasena")
        parser.add_argument("--tipo-documento", default="CC", help="Tipo de documento")
        parser.add_argument("--departamento", default="N/A", help="Departamento")
        parser.add_argument("--municipio", default="N/A", help="Municipio")
        parser.add_argument("--direccion", default="N/A", help="Direccion completa")

    def handle(self, *args, **options):
        documento = (options["documento"] or "").strip()
        email = (options["email"] or "").strip().lower()
        nombres = (options["nombres"] or "").strip()
        apellidos = (options["apellidos"] or "").strip()
        telefono = (options["telefono"] or "").strip()
        raw_password = options["password"] or ""
        tipo_documento = (options["tipo_documento"] or "CC").strip()
        departamento = (options["departamento"] or "N/A").strip()
        municipio = (options["municipio"] or "N/A").strip()
        direccion = (options["direccion"] or "N/A").strip()

        if not documento.isdigit():
            raise CommandError("El documento debe contener solo digitos.")
        if len(documento) < 8 or len(documento) > 10:
            raise CommandError("El documento debe tener entre 8 y 10 digitos.")
        if len(raw_password) < 8:
            raise CommandError("La contrasena debe tener al menos 8 caracteres.")

        User = get_user_model()

        # Unifica la cuenta auth con username=documento para el login del sistema.
        user, _ = User.objects.get_or_create(
            username=documento,
            defaults={
                "email": email,
                "first_name": nombres,
                "last_name": apellidos,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        user.email = email
        user.first_name = nombres
        user.last_name = apellidos
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(raw_password)
        user.save()

        # Evita conflictos de unicidad antes de crear/actualizar Register.
        doc_conflict = Register.objects.exclude(numero_documento=documento).filter(numero_documento=documento).exists()
        if doc_conflict:
            raise CommandError("Ya existe otro Register con ese documento.")

        email_conflict = Register.objects.exclude(numero_documento=documento).filter(correo_electronico=email).exists()
        if email_conflict:
            raise CommandError("Ya existe otro Register con ese correo.")

        tel_conflict = Register.objects.exclude(numero_documento=documento).filter(telefono=telefono).exists()
        if tel_conflict:
            raise CommandError("Ya existe otro Register con ese telefono.")

        register, created = Register.objects.get_or_create(
            numero_documento=documento,
            defaults={
                "id_usuario": user.id,
                "tipo_documento": tipo_documento,
                "nombres": nombres,
                "apellidos": apellidos,
                "correo_electronico": email,
                "telefono": telefono,
                "departamento": departamento,
                "municipio": municipio,
                "direccion_completa": direccion,
                "descripcion_perfil": "Administrador del sistema",
                "contrasena": make_password(raw_password),
                "estado": "admin",
                "admin_code_validated": True,
            },
        )

        if not created:
            register.id_usuario = user.id
            register.tipo_documento = tipo_documento
            register.nombres = nombres
            register.apellidos = apellidos
            register.correo_electronico = email
            register.telefono = telefono
            register.departamento = departamento
            register.municipio = municipio
            register.direccion_completa = direccion
            register.descripcion_perfil = register.descripcion_perfil or "Administrador del sistema"
            register.contrasena = make_password(raw_password)
            register.estado = "admin"
            register.admin_code_validated = True
            register.save()

        self.stdout.write(self.style.SUCCESS("Administrador creado/actualizado correctamente."))
        self.stdout.write(f"User.id={user.id} | Register.id={register.id} | documento={documento}")
