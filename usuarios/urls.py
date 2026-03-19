from django.urls import path
from .views import index, public_products, Logueo, register_step_1, register_step_2, olvidaste_contrasena, restablecer_contrasena, login_customer_user, mensajes_sends, logout_user, profile, update_perfil, update_perfil2, aviso_privacidad, terminos_uso, preguntas_frecuentes, marcar_mensaje_admin_leido, enviar_mensaje_admin_usuario_bloqueado
app_name = 'usuarios'

urlpatterns = [
    path('', index, name='index'),
    path('productos/', public_products, name='public_products'),
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

    path('aviso-privacidad/', aviso_privacidad, name='aviso_privacidad'),
    path('terminos-uso/', terminos_uso, name='terminos_uso'),
    path('preguntas-frecuentes/', preguntas_frecuentes, name='preguntas_frecuentes'),
    path('marcar-mensaje-admin-leido/', marcar_mensaje_admin_leido, name='marcar_mensaje_admin_leido'),
    path('enviar-mensaje-admin-usuario-bloqueado/', enviar_mensaje_admin_usuario_bloqueado, name='enviar_mensaje_admin_usuario_bloqueado'),
]
