from django.urls import path
from .views import Logueo, registrarse, olvidaste_contrasena, restablecer_contrasena

urlpatterns = [
    path('', Logueo.as_view(), name='login'),  
    path('login/', Logueo.as_view(), name='login'),
    path('register/', registrarse, name='register'),
    path('forgot-password/', olvidaste_contrasena, name='forgot_password'),
    path('reset_password/', restablecer_contrasena, name='reset_password'),
]
