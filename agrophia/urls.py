"""
URL configuration for agrophia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from usuarios.views import index, legacy_frontend_view

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('tiendas/', include('Tiendas.urls')),
    path('productos/', include('Productos.urls')),
    path('carrito/', include('carrito_compras.urls')),
    path('mensajes/', include('Mensajes.urls')),
    path('pedidos/', include('Pedidos.urls')),
    path('administrador/', include('Administrador.urls')),
    path(
        'frontend/public/views/create-shop.html',
        RedirectView.as_view(pattern_name='tiendas:create_farmer_perfil', permanent=False),
    ),
    path('frontend/public/views/<path:page>', legacy_frontend_view),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

