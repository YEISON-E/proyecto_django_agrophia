from django.urls import path

from .views import orders_client

app_name = "pedidos"

urlpatterns = [
    path("mis-pedidos/", orders_client, name="orders_client"),
]
