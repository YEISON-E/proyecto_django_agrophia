from django.urls import path

from .views import (
    orders_client,
    orders_farmer,
    update_order_status,
    cancel_order,
    order_receipt,
    order_farmer_detail,
)

app_name = "pedidos"

urlpatterns = [
    path("mis-pedidos/", orders_client, name="orders_client"),
    path("pedidos-farmer/", orders_farmer, name="orders_farmer"),
    path("pedidos-farmer/<int:order_id>/detalle/", order_farmer_detail, name="order_farmer_detail"),
    path("pedidos-farmer/<int:order_id>/status/", update_order_status, name="update_order_status"),
    path("mis-pedidos/<int:order_id>/cancelar/", cancel_order, name="cancel_order"),
    path("mis-pedidos/<int:order_id>/comprobante/", order_receipt, name="order_receipt"),
]
