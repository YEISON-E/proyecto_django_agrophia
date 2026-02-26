from django.urls import path

from .views import (
    create_farmer_perfil,
    interface_farmer,
    create_product,
    create_shop_step1,
    create_shop_step2,
)

app_name = "tiendas"

urlpatterns = [
    path("interface-farmer/", interface_farmer, name="interface_farmer"),
    path("create-product/", create_product, name="create_product"),
    path("create-farmer-perfil/", create_farmer_perfil, name="create_farmer_perfil"),
    path("create-shop/", create_shop_step1, name="create_shop_step1"),
    path("create-shop/step2/", create_shop_step2, name="create_shop_step2"),
]
