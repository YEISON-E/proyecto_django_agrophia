from django.urls import path
from .views import Logueo

urlpatterns = [
    path('', Logueo.as_view(), name='login'),  
    path('login/', Logueo.as_view(), name='forloggin'),
]
