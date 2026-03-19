import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from Mensajes.models import AdminToUserMessage
from usuarios.models import Register


class AdminBulkMessageTests(TestCase):
	def setUp(self):
		self.admin_user = User.objects.create_user(
			username="admin001",
			password="Admin123!",
			email="admin@test.com",
		)
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

		self.client.force_login(self.admin_user)
		session = self.client.session
		session["admin_user_id"] = self.admin_user.id
		session.save()

		self.url = reverse("administrador:usuario_admin_enviar_mensaje_general")

	def test_bulk_message_success_all(self):
		payload = {
			"mensaje": "Mensaje general de prueba",
			"destinatario": "all",
		}
		response = self.client.post(
			self.url,
			data=json.dumps(payload),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertTrue(body["ok"])
		self.assertEqual(body["enviados"], Register.objects.count())
		self.assertEqual(AdminToUserMessage.objects.count(), Register.objects.count())

	def test_bulk_message_invalid_json_returns_400(self):
		response = self.client.post(
			self.url,
			data="{mensaje:}",
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.json()["ok"])

	def test_bulk_message_invalid_recipient_returns_400(self):
		payload = {
			"mensaje": "Mensaje general de prueba",
			"destinatario": "invalid_value",
		}
		response = self.client.post(
			self.url,
			data=json.dumps(payload),
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.json()["ok"])
