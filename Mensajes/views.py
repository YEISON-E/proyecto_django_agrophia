from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.utils import timezone

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
		return redirect("usuarios:login_customer_user")

	messages_received = CustomerMessage.objects.select_related("product", "sender").filter(receiver=request.user)
	messages_received = messages_received.prefetch_related("farmer_replies")
	return render(request, "mensajes/farmer_messages.html", {
		"messages_received": messages_received,
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
		product = Product.objects.select_related("owner").get(pk=int(product_id))
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
		return redirect("mensajes:farmer_messages")

	reply_content = (request.POST.get("reply") or "").strip()
	if not reply_content:
		return redirect("mensajes:farmer_messages")

	FarmerReply.objects.create(
		message=message,
		content=reply_content,
	)

	message.reply_content = reply_content
	message.status = CustomerMessage.STATUS_REPLIED
	message.replied_at = timezone.now()
	message.save(update_fields=["reply_content", "status", "replied_at"])

	return redirect("mensajes:farmer_messages")
