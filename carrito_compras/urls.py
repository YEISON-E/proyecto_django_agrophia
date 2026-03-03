from django.urls import path

from .views import shopping_cart

app_name = "carrito_compras"

urlpatterns = [
    path("shopping-cart/", shopping_cart, name="shopping_cart"),
]
