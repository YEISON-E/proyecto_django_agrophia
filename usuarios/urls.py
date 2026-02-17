from django.urls import path
from .views import index, Logueo, register_step_1, register_step_2, olvidaste_contrasena, restablecer_contrasena, create_shop_step1, create_shop_step2
from .views import login_view

urlpatterns = [
    path('', index, name='index'),
    path('index/', index, name='index'),
    path('login/', Logueo.as_view(), name='login'),

    path('register/', register_step_1, name='register'),
    path('register/step-2/', register_step_2, name='register2'),


    path('forgot-password/', olvidaste_contrasena, name='forgot_password'),
    path('reset_password/', restablecer_contrasena, name='reset_password'),

    path("create-shop/", create_shop_step1, name="create_shop_step1"),
    path("create-shop/step2/", create_shop_step2, name="create_shop_step2"),

]


