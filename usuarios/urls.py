from django.urls import path
from .views import index, Logueo, register_step_1, register_step_2, olvidaste_contrasena, restablecer_contrasena, login_customer_user, mensajes_sends, logout_user, profile, update_perfil, update_perfil2
app_name = 'usuarios'

urlpatterns = [
    path('', index, name='index'),
    path('login/', Logueo.as_view(), name='login'),
    path('home/', login_customer_user, name='home_customer'),
    path('login-customer-user/', login_customer_user, name='login_customer_user'),
    path('mensajes-sends/', mensajes_sends, name='mensajes_sends'),
    path('profile/', profile, name='profile'),
    path('update-perfil/', update_perfil, name='update_perfil'),
    path('update-perfil2/', update_perfil2, name='update_perfil2'),

    path('register/', register_step_1, name='register'),
    path('register/step-2/', register_step_2, name='register2'),
    
    path('forgot-password/', olvidaste_contrasena, name='forgot_password'),
    path('reset_password/', restablecer_contrasena, name='reset_password'),

    path('logout/', logout_user, name='logout'),

]
