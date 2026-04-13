"""
Vistas del modulo de mensajeria.

Este archivo cubre comunicacion entre cliente y agricultor, incluyendo:
- Conversaciones de mensajes enviados por clientes.
- Bandeja de entrada para agricultores con conversacion por remitente.
- Respuestas individuales y por conversacion.
- Rechazo de mensajes y actualizacion de estados.
- Envio de mensajes desde detalle de producto via peticiones asincronas.

Objetivo funcional:
Mantener trazabilidad del intercambio (mensaje base y respuestas) para mostrar
un historial de chat ordenado cronologicamente.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
# Importación de dependencias necesarias para ejecutar esta vista.
from django.utils import timezone
from django.urls import reverse

from Tiendas.views import user_has_shop
from Productos.models import Product
from .models import CustomerMessage, FarmerReply

# Create your views here.


@never_cache
def sent_messages(request):
	"""Muestra conversaciones iniciadas por el cliente autenticado.

	Agrupa mensajes por vendedor y producto para construir un historial tipo
	chat con orden cronologico y seleccion de conversacion activa.
	"""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	messages_sent = CustomerMessage.objects.select_related("product", "receiver").filter(sender=request.user)
	messages_sent = messages_sent.prefetch_related("farmer_replies").order_by("created_at")
	request.session.pop("sent_messages_notice", None)

	# 1) Agrupa mensajes por (vendedor, producto) para representar conversaciones.
	conversations_by_key = {}
	for message in messages_sent:
		key = (message.receiver_id, message.product_id)
		conversation = conversations_by_key.get(key)
		# Control de flujo y validación de condiciones del proceso.
		if not conversation:
			conversation = {
				"receiver": message.receiver,
				"product": message.product,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"base_messages": [],
				"chat_items": [],
				"last_message_at": message.created_at,
				"last_preview": "",
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			}
			conversations_by_key[key] = conversation

		conversation["base_messages"].append(message)

	# 2) Convierte cada conversacion a una secuencia de chat cronologica.
	for conversation in conversations_by_key.values():
		items = []
		for message in conversation["base_messages"]:
			items.append({
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"kind": "customer",
				"content": message.content,
				"created_at": message.created_at,
				"status": message.status,
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"message": message,
			})
			for reply in message.farmer_replies.all():
				items.append({
					# Paso de apoyo dentro del flujo principal de la funcionalidad.
					"kind": "farmer",
					"content": reply.content,
					"created_at": reply.created_at,
					"status": None,
					# Paso de apoyo dentro del flujo principal de la funcionalidad.
					"message": message,
				})

		items.sort(key=lambda item: item["created_at"])
		conversation["chat_items"] = items
		if items:
			conversation["last_message_at"] = items[-1]["created_at"]
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			conversation["last_preview"] = (items[-1]["content"] or "").strip()[:60]

		last_base_message = conversation["base_messages"][-1]
		status = (last_base_message.status or "").strip().lower()
		status_label_map = {
			CustomerMessage.STATUS_PENDING: "Sin respuesta",
			CustomerMessage.STATUS_REPLIED: "Respondido",
			CustomerMessage.STATUS_REJECTED: "Rechazado",
		}
		conversation["last_status"] = status
		conversation["last_status_label"] = status_label_map.get(status, "")

	# 3) Ordena conversaciones por actividad reciente y resuelve seleccion activa.
	conversations = sorted(
		conversations_by_key.values(),
		key=lambda item: item["last_message_at"],
		reverse=True,
	# Paso de apoyo dentro del flujo principal de la funcionalidad.
	)

	selected_receiver = (request.GET.get("receiver") or "").strip()
	selected_product = (request.GET.get("product") or "").strip()
	list_mode = (request.GET.get("view") or "").strip().lower() == "list"
	selected_conversation = None
	if not list_mode and selected_receiver.isdigit() and selected_product.isdigit():
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		selected_conversation = conversations_by_key.get((int(selected_receiver), int(selected_product)))

	# 4) Prepara payload final para render del panel izquierdo + chat.
	chat_items = selected_conversation["chat_items"] if selected_conversation else []
	selected_base_message_id = None
	if selected_conversation and selected_conversation["base_messages"]:
		selected_base_message_id = selected_conversation["base_messages"][-1].id

	return render(request, "mensajes/sent_messages.html", {
		"conversations": conversations,
		"selected_conversation": selected_conversation,
		"chat_items": chat_items,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"selected_base_message_id": selected_base_message_id,
	})


@require_POST
def delete_sent_message(request, message_id):
	"""Elimina un mensaje enviado por el cliente propietario del registro."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	message = get_object_or_404(CustomerMessage, pk=message_id, sender=request.user)
	message.delete()

	return redirect("mensajes:sent_messages")


@require_POST
def delete_sent_conversation(request):
	"""Elimina todo el chat del cliente con un vendedor para un producto."""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	receiver_id = (request.POST.get("receiver_id") or "").strip()
	product_id = (request.POST.get("product_id") or "").strip()

	if not receiver_id.isdigit() or not product_id.isdigit():
		request.session["sent_messages_notice"] = "No se pudo eliminar el chat seleccionado."
		return redirect("mensajes:sent_messages")

	deleted_count, _ = CustomerMessage.objects.filter(
		sender=request.user,
		receiver_id=int(receiver_id),
		product_id=int(product_id),
	).delete()

	if deleted_count:
		request.session["sent_messages_notice"] = "Chat eliminado correctamente."
	else:
		request.session["sent_messages_notice"] = "No se encontraron mensajes para eliminar."

	return redirect("mensajes:sent_messages")


@require_POST
def delete_farmer_conversation(request):
	"""Elimina toda la conversacion del vendedor con un cliente remitente."""
	if not request.user.is_authenticated:
		return redirect("usuarios:login")
	if not user_has_shop(request.user):
		return redirect("usuarios:home_customer")

	sender_id = (request.POST.get("sender_id") or "").strip()
	if not sender_id.isdigit():
		return redirect("mensajes:farmer_messages")

	CustomerMessage.objects.filter(
		receiver=request.user,
		sender_id=int(sender_id),
	).delete()

	return redirect(f"{reverse('mensajes:farmer_messages')}?view=list")


@require_POST
def customer_reply_message(request, message_id):
	"""Permite al cliente responder una conversacion ya existente."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	base_message = get_object_or_404(CustomerMessage, pk=message_id, sender=request.user)
	reply_content = (request.POST.get("reply") or "").strip()

	if not reply_content:
		request.session["sent_messages_notice"] = "Escribe un mensaje para responder."
		return redirect("mensajes:sent_messages")

	if len(reply_content) > 500:
		request.session["sent_messages_notice"] = "La respuesta no debe superar 500 caracteres."
		return redirect("mensajes:sent_messages")

	CustomerMessage.objects.create(
		sender=request.user,
		receiver=base_message.receiver,
		product=base_message.product,
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		content=reply_content,
	)

	request.session["sent_messages_notice"] = "Respuesta enviada al vendedor."
	return redirect(f"{reverse('mensajes:sent_messages')}?receiver={base_message.receiver_id}&product={base_message.product_id}")


@never_cache
def farmer_messages(request):
	"""Lista la bandeja de conversaciones para el agricultor autenticado.

	Agrupa por remitente, calcula mensajes pendientes y selecciona el chat
	activo segun querystring o el mas reciente por defecto.
	"""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")
	if not user_has_shop(request.user):
		return redirect("usuarios:home_customer")

	messages_received = CustomerMessage.objects.select_related("product", "sender").filter(
		receiver=request.user,
	).prefetch_related("farmer_replies")

	# 1) Agrupa la bandeja por remitente y calcula pendientes por conversacion.
	conversations_by_sender = {}
	for message in messages_received:
		sender_id = message.sender_id
		conversation = conversations_by_sender.get(sender_id)
		# Control de flujo y validación de condiciones del proceso.
		if not conversation:
			conversation = {
				"sender": message.sender,
				"messages": [],
				# Paso de apoyo dentro del flujo principal de la funcionalidad.
				"unread_count": 0,
				"last_message_at": message.created_at,
				"last_preview": "",
			}
			# Paso de apoyo dentro del flujo principal de la funcionalidad.
			conversations_by_sender[sender_id] = conversation

		conversation["messages"].append(message)
		if message.status == CustomerMessage.STATUS_PENDING:
			conversation["unread_count"] += 1

		if message.created_at >= conversation["last_message_at"]:
			conversation["last_message_at"] = message.created_at
			conversation["last_preview"] = (message.content or "").strip()[:60]

	# 2) Orden cronologico interno de cada chat + orden global por recencia.
	for conversation in conversations_by_sender.values():
		conversation["messages"].sort(key=lambda item: item.created_at)
		last_message = conversation["messages"][-1]
		status = (last_message.status or "").strip().lower()
		status_label_map = {
			CustomerMessage.STATUS_PENDING: "Sin respuesta",
			CustomerMessage.STATUS_REPLIED: "Respondido",
			CustomerMessage.STATUS_REJECTED: "Rechazado",
		}
		conversation["last_status"] = status
		conversation["last_status_label"] = status_label_map.get(status, "")

	conversations = sorted(
		conversations_by_sender.values(),
		key=lambda item: item["last_message_at"],
		reverse=True,
	# Paso de apoyo dentro del flujo principal de la funcionalidad.
	)

	requested_chat = (request.GET.get("chat") or "").strip()
	list_mode = (request.GET.get("view") or "").strip().lower() == "list"
	selected_chat_id = None
	if list_mode:
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		selected_chat_id = None
	elif requested_chat.isdigit() and int(requested_chat) in conversations_by_sender:
		selected_chat_id = int(requested_chat)

	# 3) Renderiza lista de conversaciones y panel de chat seleccionado.
	selected_conversation = conversations_by_sender.get(selected_chat_id)
	selected_messages = selected_conversation["messages"] if selected_conversation else []

	return render(request, "mensajes/farmer_messages.html", {
		"conversations": conversations,
		"selected_chat_id": selected_chat_id,
		"selected_conversation": selected_conversation,
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		"selected_messages": selected_messages,
	})


@require_POST
def send_message(request):
	"""Crea un mensaje de cliente hacia el propietario de un producto."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return JsonResponse({"ok": False, "message": "No autenticado."}, status=401)

	product_id = (request.POST.get("product_id") or "").strip()
	content = (request.POST.get("message") or "").strip()

	if not product_id or not content:
		return JsonResponse({"ok": False, "message": "Datos inválidos."}, status=400)

	if len(content) > 500:
		return JsonResponse({"ok": False, "message": "El mensaje no debe superar 500 caracteres."}, status=400)

	try:
		product = Product.objects.select_related("owner", "shop").get(
			pk=int(product_id),
			is_active=True,
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			shop__is_active=True,
		)
	except (ValueError, Product.DoesNotExist):
		return JsonResponse({"ok": False, "message": "Producto no encontrado."}, status=404)

	if product.owner_id == request.user.id:
		return JsonResponse({"ok": False, "message": "No puedes enviarte mensajes a ti mismo."}, status=400)

	CustomerMessage.objects.create(
		sender=request.user,
		receiver=product.owner,
		product=product,
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		content=content,
	)

	return JsonResponse({"ok": True})


@require_POST
def reply_message(request, message_id):
	"""Registra respuesta o rechazo del agricultor a un mensaje puntual."""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	message = get_object_or_404(CustomerMessage, pk=message_id, receiver=request.user)
	action = (request.POST.get("action") or "reply").strip().lower()

	if action == "reject":
		message.status = CustomerMessage.STATUS_REJECTED
		message.reply_content = ""
		message.replied_at = timezone.now()
		# Paso de apoyo dentro del flujo principal de la funcionalidad.
		message.save(update_fields=["status", "reply_content", "replied_at"])
		return redirect(f"{reverse('mensajes:farmer_messages')}?chat={message.sender_id}")

	reply_content = (request.POST.get("reply") or "").strip()
	if not reply_content:
		return redirect(f"{reverse('mensajes:farmer_messages')}?chat={message.sender_id}")

	FarmerReply.objects.create(
		message=message,
		content=reply_content,
	)

	message.reply_content = reply_content
	message.status = CustomerMessage.STATUS_REPLIED
	message.replied_at = timezone.now()
	message.save(update_fields=["reply_content", "status", "replied_at"])

	return redirect(f"{reverse('mensajes:farmer_messages')}?chat={message.sender_id}")


@require_POST
def reply_conversation(request, sender_id):
	"""Responde o rechaza en bloque los pendientes de una conversacion.

	La respuesta se asocia al ultimo mensaje de la conversacion para mantener
	trazabilidad del hilo.
	"""
	# Flujo: valida entrada y reglas de negocio para mantener consistencia funcional.
	# Respuesta: retorna render, redirect o JSON según el resultado de la operación.
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	conversation_qs = CustomerMessage.objects.filter(
		receiver=request.user,
		sender_id=sender_id,
	).order_by("created_at")

	if not conversation_qs.exists():
		return redirect("mensajes:farmer_messages")

	latest_message = conversation_qs.last()
	action = (request.POST.get("action") or "reply").strip().lower()

	if action == "reject":
		pending_messages = conversation_qs.filter(status=CustomerMessage.STATUS_PENDING)
		now = timezone.now()
		pending_messages.update(
			# Actualización de estado intermedio que será utilizada en pasos posteriores.
			status=CustomerMessage.STATUS_REJECTED,
			reply_content="",
			replied_at=now,
		)
		# Retorno de respuesta según el estado y resultado de la operación.
		return redirect(f"{reverse('mensajes:farmer_messages')}?chat={sender_id}")

	reply_content = (request.POST.get("reply") or "").strip()
	if not reply_content:
		return redirect(f"{reverse('mensajes:farmer_messages')}?chat={sender_id}")

	FarmerReply.objects.create(
		message=latest_message,
		content=reply_content,
	)

	now = timezone.now()
	conversation_qs.filter(status=CustomerMessage.STATUS_PENDING).update(
		reply_content=reply_content,
		status=CustomerMessage.STATUS_REPLIED,
		# Actualización de estado intermedio que será utilizada en pasos posteriores.
		replied_at=now,
	)

	return redirect(f"{reverse('mensajes:farmer_messages')}?chat={sender_id}")
