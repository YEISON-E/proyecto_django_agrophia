from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import index, Logueo, register_step_1, register_step_2, olvidaste_contrasena, restablecer_contrasena, create_shop_step1, create_shop_step2, login_customer_user
app_name = 'usuarios'

urlpatterns = [
    path('', index, name='index'),
    path('login/', Logueo.as_view(), name='login'),
    path('login-customer-user/', login_customer_user, name='login_customer_user'),

    path('register/', register_step_1, name='register'),
    path('register/step-2/', register_step_2, name='register2'),
    
    path('forgot-password/', olvidaste_contrasena, name='forgot_password'),
    path('reset_password/', restablecer_contrasena, name='reset_password'),

    path('logout/', LogoutView.as_view(next_page='/usuarios/'), name='logout'),

    path("create-shop/", create_shop_step1, name="create_shop_step1"),
    path("create-shop/step2/", create_shop_step2, name="create_shop_step2"),

]
