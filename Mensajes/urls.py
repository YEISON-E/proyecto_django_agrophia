from django.urls import path

from .views import sent_messages, farmer_messages, send_message, reply_message

app_name = "mensajes"

urlpatterns = [
    path("enviados/", sent_messages, name="sent_messages"),
    path("recibidos-agricultor/", farmer_messages, name="farmer_messages"),
    path("enviar/", send_message, name="send_message"),
    path("responder/<int:message_id>/", reply_message, name="reply_message"),
]
