from django.urls import path

from .views import (
    create_product,
    create_product2,
    descripcion_product,
    disabled_products,
)

app_name = "productos"

urlpatterns = [
    path("create-product/", create_product, name="create_product"),
    path("create-product/step2/", create_product2, name="create_product2"),
    path("disabled-products/", disabled_products, name="disabled_products"),
    path("descripcion-product/<int:product_id>/", descripcion_product, name="descripcion_product"),
]
