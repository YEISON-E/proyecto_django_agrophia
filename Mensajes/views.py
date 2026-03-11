from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse

from Tiendas.views import user_has_shop
from Productos.models import Product
from .models import CustomerMessage, FarmerReply

# Create your views here.


@never_cache
def sent_messages(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	messages_sent = CustomerMessage.objects.select_related("product", "receiver").filter(sender=request.user)
	messages_sent = messages_sent.prefetch_related("farmer_replies")
	return render(request, "mensajes/sent_messages.html", {
		"messages_sent": messages_sent,
	})


@never_cache
def farmer_messages(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")
	if not user_has_shop(request.user):
		return redirect("usuarios:home_customer")

	messages_received = CustomerMessage.objects.select_related("product", "sender").filter(
		receiver=request.user,
	).prefetch_related("farmer_replies")

	conversations_by_sender = {}
	for message in messages_received:
		sender_id = message.sender_id
		conversation = conversations_by_sender.get(sender_id)
		if not conversation:
			conversation = {
				"sender": message.sender,
				"messages": [],
				"unread_count": 0,
				"last_message_at": message.created_at,
				"last_preview": "",
			}
			conversations_by_sender[sender_id] = conversation

		conversation["messages"].append(message)
		if message.status == CustomerMessage.STATUS_PENDING:
			conversation["unread_count"] += 1

		if message.created_at >= conversation["last_message_at"]:
			conversation["last_message_at"] = message.created_at
			conversation["last_preview"] = (message.content or "").strip()[:60]

	for conversation in conversations_by_sender.values():
		conversation["messages"].sort(key=lambda item: item.created_at)

	conversations = sorted(
		conversations_by_sender.values(),
		key=lambda item: item["last_message_at"],
		reverse=True,
	)

	requested_chat = (request.GET.get("chat") or "").strip()
	selected_chat_id = None
	if requested_chat.isdigit() and int(requested_chat) in conversations_by_sender:
		selected_chat_id = int(requested_chat)
	elif conversations:
		selected_chat_id = conversations[0]["sender"].id

	selected_conversation = conversations_by_sender.get(selected_chat_id)
	selected_messages = selected_conversation["messages"] if selected_conversation else []

	return render(request, "mensajes/farmer_messages.html", {
		"conversations": conversations,
		"selected_chat_id": selected_chat_id,
		"selected_conversation": selected_conversation,
		"selected_messages": selected_messages,
	})


@require_POST
def send_message(request):
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
		content=content,
	)

	return JsonResponse({"ok": True})


@require_POST
def reply_message(request, message_id):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")

	message = get_object_or_404(CustomerMessage, pk=message_id, receiver=request.user)
	action = (request.POST.get("action") or "reply").strip().lower()

	if action == "reject":
		message.status = CustomerMessage.STATUS_REJECTED
		message.reply_content = ""
		message.replied_at = timezone.now()
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
			status=CustomerMessage.STATUS_REJECTED,
			reply_content="",
			replied_at=now,
		)
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
		replied_at=now,
	)

	return redirect(f"{reverse('mensajes:farmer_messages')}?chat={sender_id}")
