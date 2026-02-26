from django.urls import path
from .views import index, Logueo, register_step_1, register_step_2, olvidaste_contrasena, restablecer_contrasena, create_shop_step1, create_shop_step2, login_customer_user, logout_user, create_farmer_perfil, interface_farmer, create_product, profile, update_perfil, update_perfil2
app_name = 'usuarios'

urlpatterns = [
    path('', index, name='index'),
    path('login/', Logueo.as_view(), name='login'),
    path('login-customer-user/', login_customer_user, name='login_customer_user'),
    path('interface-farmer/', interface_farmer, name='interface_farmer'),
    path('create-product/', create_product, name='create_product'),
    path('create-farmer-perfil/', create_farmer_perfil, name='create_farmer_perfil'),
    path('profile/', profile, name='profile'),
    path('update-perfil/', update_perfil, name='update_perfil'),
    path('update-perfil2/', update_perfil2, name='update_perfil2'),

    path('register/', register_step_1, name='register'),
    path('register/step-2/', register_step_2, name='register2'),
    
    path('forgot-password/', olvidaste_contrasena, name='forgot_password'),
    path('reset_password/', restablecer_contrasena, name='reset_password'),

    path('logout/', logout_user, name='logout'),

    path("create-shop/", create_shop_step1, name="create_shop_step1"),
    path("create-shop/step2/", create_shop_step2, name="create_shop_step2"),

]
