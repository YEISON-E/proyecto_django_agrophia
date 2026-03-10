from django.urls import path

from .views import (
    create_product,
    create_product2,
    descripcion_product,
    review_product_farmer,
    update_product,
    disable_product,
    disabled_products,
    activate_product,
)

app_name = "productos"

urlpatterns = [
    path("create-product/", create_product, name="create_product"),
    path("create-product/step2/", create_product2, name="create_product2"),
    path("disabled-products/", disabled_products, name="disabled_products"),
    path("review-product-farmer/<int:product_id>/", review_product_farmer, name="review_product_farmer"),
    path("update-product/<int:product_id>/", update_product, name="update_product"),
    path("review-product-farmer/<int:product_id>/disable/", disable_product, name="disable_product"),
    path("disabled-products/<int:product_id>/activate/", activate_product, name="activate_product"),
    path("descripcion-product/<int:product_id>/", descripcion_product, name="descripcion_product"),
]
