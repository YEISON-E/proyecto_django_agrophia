from django.urls import path

from .views import shopping_cart, add_to_cart, remove_from_cart, update_cart_quantity, checkout

app_name = "carrito_compras"

urlpatterns = [
    path("shopping-cart/", shopping_cart, name="shopping_cart"),
    path("add/", add_to_cart, name="add_to_cart"),
    path("remove/<int:product_id>/", remove_from_cart, name="remove_from_cart"),
    path("update/<int:product_id>/", update_cart_quantity, name="update_cart_quantity"),
    path("checkout/", checkout, name="checkout"),
]
