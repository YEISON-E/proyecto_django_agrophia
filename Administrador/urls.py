from django.urls import path
from . import views

app_name = 'administrador'

urlpatterns = [
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
    path('home/', views.home_admin_view, name='home_admin'),
    path('usuarios/', views.usuarios_admin_view, name='usuarios_admin'),
    path('pedidos/', views.orders_page_view, name='orders_page'),
    path('tiendas/', views.store_admin_view, name='store_admin'),
    path('productos/', views.producs_page_view, name='producs_page'),
    path('usuarios/<int:usuario_id>/', views.usuario_admin_detalle_view, name='usuario_admin_detalle'),
    path('usuarios/<int:usuario_id>/editar/', views.usuario_admin_editar_view, name='usuario_admin_editar'),
    path('usuarios/<int:usuario_id>/block/', views.usuario_admin_block_view, name='usuario_admin_block'),
    path('usuarios/<int:usuario_id>/unblock/', views.usuario_admin_unblock_view, name='usuario_admin_unblock'),
    path('usuarios/<int:usuario_id>/enviar_mensaje/', views.usuario_admin_enviar_mensaje_view, name='usuario_admin_enviar_mensaje'),
    path('usuarios/enviar_mensaje/', views.usuario_admin_enviar_mensaje_general_view, name='usuario_admin_enviar_mensaje_general'),
    path('usuarios/reporte/', views.reporte_usuarios_view, name='reporte_usuarios'),
    path('usuarios/crear/', views.usuario_admin_crear_view, name='usuario_admin_crear'),
    path('editar-perfil/', views.admin_editar_perfil_view, name='admin_editar_perfil'),
]
