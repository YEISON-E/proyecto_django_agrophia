from django.urls import path
from .views import Logueo, registrarse

urlpatterns = [
    path('', Logueo.as_view(), name='login'),  
    path('login/', Logueo.as_view(), name='login'),
    path('register/', registrarse, name='register'),
]
