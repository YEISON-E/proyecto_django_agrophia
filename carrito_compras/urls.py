from django.urls import path

from .views import shopping_cart, add_to_cart, remove_from_cart

app_name = "carrito_compras"

urlpatterns = [
    path("shopping-cart/", shopping_cart, name="shopping_cart"),
    path("add/", add_to_cart, name="add_to_cart"),
    path("remove/<int:product_id>/", remove_from_cart, name="remove_from_cart"),
]
