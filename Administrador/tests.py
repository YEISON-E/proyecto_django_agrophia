import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from Mensajes.models import AdminToUserMessage
from usuarios.models import Register


# Pruebas del flujo de envio masivo de mensajes desde el panel admin.
class AdminBulkMessageTests(TestCase):
	def setUp(self):
		# Crea el usuario admin que ejecuta la accion.
		self.admin_user = User.objects.create_user(
			username="admin001",
			password="Admin123!",
			email="admin@test.com",
		)
		# Crea su perfil Register con rol admin y 2FA validado.
		self.admin_register = Register.objects.create(
			id_usuario=self.admin_user.id,
			tipo_documento="CC",
			numero_documento="100000001",
			nombres="Admin",
			apellidos="Principal",
			correo_electronico="admin@test.com",
			telefono="300000001",
			departamento="Antioquia",
			municipio="Medellin",
			direccion_completa="Dir admin",
			contrasena="Admin123!",
			estado="admin",
			admin_code_validated=True,
		)

		# Crea usuarios clientes destino para la mensajeria masiva.
		self.user_1 = User.objects.create_user(
			username="cliente01",
			password="Cliente123!",
			email="cliente01@test.com",
		)
		self.user_2 = User.objects.create_user(
			username="cliente02",
			password="Cliente123!",
			email="cliente02@test.com",
		)

		# Crea el perfil extendido de cada cliente en Register.
		Register.objects.create(
			id_usuario=self.user_1.id,
			tipo_documento="CC",
			numero_documento="100000002",
			nombres="Cliente",
			apellidos="Uno",
			correo_electronico="cliente01@test.com",
			telefono="300000002",
			departamento="Antioquia",
			municipio="Medellin",
			direccion_completa="Dir 1",
			contrasena="Cliente123!",
			estado="activo",
		)
		Register.objects.create(
			id_usuario=self.user_2.id,
			tipo_documento="CC",
			numero_documento="100000003",
			nombres="Cliente",
			apellidos="Dos",
			correo_electronico="cliente02@test.com",
			telefono="300000003",
			departamento="Antioquia",
			municipio="Medellin",
			direccion_completa="Dir 2",
			contrasena="Cliente123!",
			estado="activo",
		)

		# Simula login del admin y marca sesion esperada por middleware/admin.
		self.client.force_login(self.admin_user)
		session = self.client.session
		session["admin_user_id"] = self.admin_user.id
		session.save()

		# Endpoint a probar: envio de mensaje general a usuarios.
		self.url = reverse("administrador:usuario_admin_enviar_mensaje_general")

	def test_bulk_message_success_all(self):
		# Caso exitoso: mensaje valido con destinatario "all".
		payload = {
			"mensaje": "Mensaje general de prueba",
			"destinatario": "all",
		}
		response = self.client.post(
			self.url,
			data=json.dumps(payload),
			content_type="application/json",
		)

		# Valida respuesta OK y cantidad de mensajes creados en BD.
		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertTrue(body["ok"])
		self.assertEqual(body["enviados"], Register.objects.count())
		self.assertEqual(AdminToUserMessage.objects.count(), Register.objects.count())

	def test_bulk_message_invalid_json_returns_400(self):
		# Caso de error: body JSON mal formado.
		response = self.client.post(
			self.url,
			data="{mensaje:}",
			content_type="application/json",
		)

		# Debe responder 400 y ok=False.
		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.json()["ok"])

	def test_bulk_message_invalid_recipient_returns_400(self):
		# Caso de error: valor de destinatario fuera de los permitidos.
		payload = {
			"mensaje": "Mensaje general de prueba",
			"destinatario": "invalid_value",
		}
		response = self.client.post(
			self.url,
			data=json.dumps(payload),
			content_type="application/json",
		)

		# Debe responder 400 y marcar la operacion como no exitosa.
		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.json()["ok"])
