from django.urls import path
from .views import Logueo, registrarse
from .views import login_view

urlpatterns = [
    path('', Logueo.as_view(), name='login'),  
    path('register/', registrarse, name='register'),
]
