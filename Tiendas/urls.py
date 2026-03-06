from django.urls import path

from .views import (
    create_farmer_perfil,
    interface_farmer,
    profile_shop,
    disable_shop,
    activate_shop,
    update_shop_step1,
    update_shop_step2,
    mensajes_farmer,
    create_product,
    create_product2,
    create_shop_step1,
    create_shop_step2,
)

app_name = "tiendas"

urlpatterns = [
    path("interface-farmer/", interface_farmer, name="interface_farmer"),
    path("profile-shop/", profile_shop, name="profile_shop"),
    path("disable-shop/", disable_shop, name="disable_shop"),
    path("activate-shop/", activate_shop, name="activate_shop"),
    path("update-shop/", update_shop_step1, name="update_shop_step1"),
    path("update-shop/step2/", update_shop_step2, name="update_shop_step2"),
    path("mensajes-farmer/", mensajes_farmer, name="mensajes_farmer"),
    path("create-product/", create_product, name="create_product"),
    path("create-product/step2/", create_product2, name="create_product2"),
    path("create-farmer-perfil/", create_farmer_perfil, name="create_farmer_perfil"),
    path("create-shop/", create_shop_step1, name="create_shop_step1"),
    path("create-shop/step2/", create_shop_step2, name="create_shop_step2"),
]
