# Importa la funcion path para declarar rutas URL.
from django.urls import path
# Importa las vistas del modulo administrador.
from . import views

# Define el namespace de estas rutas para usar nombres como administrador:home_admin.
app_name = 'administrador'

# Lista principal de rutas del panel administrativo.
urlpatterns = [
    # Ruta para validar el codigo de seguridad del administrador (2FA).
    path('verificar-codigo/', views.admin_verify_code_view, name='admin_verify_code'),
    # Ruta para cerrar sesion del administrador.
    path('logout/', views.admin_logout_view, name='admin_logout'),
    # Ruta de inicio del panel admin.
    path('home/', views.home_admin_view, name='home_admin'),
    # Ruta para generar/revisar el reporte de actividad reciente del admin.
    path('home/reporte-actividad/', views.reporte_actividad_reciente_view, name='reporte_actividad_reciente'),
    # Ruta para listar usuarios en el panel admin.
    path('usuarios/', views.usuarios_admin_view, name='usuarios_admin'),
    # Ruta para listar pedidos en el panel admin.
    path('pedidos/', views.orders_page_view, name='orders_page'),
    # Ruta para listar tiendas en el panel admin.
    path('tiendas/', views.store_admin_view, name='store_admin'),
    # Ruta para crear una nueva tienda desde admin.
    path('tiendas/crear/', views.tienda_admin_crear_view, name='tienda_admin_crear'),
    # Ruta para ver el detalle de una tienda especifica por ID.
    path('tiendas/<int:tienda_id>/', views.tienda_admin_detalle_view, name='tienda_admin_detalle'),
    # Ruta para ver productos de una tienda especifica.
    path('tiendas/<int:tienda_id>/productos/', views.tienda_admin_productos_view, name='tienda_admin_productos'),
    # Ruta para editar una tienda especifica.
    path('tiendas/<int:tienda_id>/editar/', views.tienda_admin_editar_view, name='tienda_admin_editar'),
    # Ruta para bloquear una tienda especifica.
    path('tiendas/<int:tienda_id>/block/', views.tienda_admin_block_view, name='tienda_admin_block'),
    # Ruta para desbloquear una tienda especifica.
    path('tiendas/<int:tienda_id>/unblock/', views.tienda_admin_unblock_view, name='tienda_admin_unblock'),
    # Ruta para generar reporte de tiendas.
    path('tiendas/reporte/', views.reporte_tiendas_view, name='reporte_tiendas'),
    # Ruta para listar productos en el panel admin.
    path('productos/', views.producs_page_view, name='producs_page'),
    # Ruta para ver detalle de un usuario por ID.
    path('usuarios/<int:usuario_id>/', views.usuario_admin_detalle_view, name='usuario_admin_detalle'),
    # Ruta para editar un usuario por ID.
    path('usuarios/<int:usuario_id>/editar/', views.usuario_admin_editar_view, name='usuario_admin_editar'),
    # Ruta para enviar correo de recuperacion a un usuario especifico.
    path('usuarios/<int:usuario_id>/enviar_recuperacion/', views.usuario_admin_enviar_recuperacion_view, name='usuario_admin_enviar_recuperacion'),
    # Ruta para bloquear un usuario especifico.
    path('usuarios/<int:usuario_id>/block/', views.usuario_admin_block_view, name='usuario_admin_block'),
    # Ruta para desbloquear un usuario especifico.
    path('usuarios/<int:usuario_id>/unblock/', views.usuario_admin_unblock_view, name='usuario_admin_unblock'),
    # Ruta para enviar mensaje desde admin a un usuario especifico.
    path('usuarios/<int:usuario_id>/enviar_mensaje/', views.usuario_admin_enviar_mensaje_view, name='usuario_admin_enviar_mensaje'),
    # Ruta para enviar mensaje general/masivo a usuarios.
    path('usuarios/enviar_mensaje/', views.usuario_admin_enviar_mensaje_general_view, name='usuario_admin_enviar_mensaje_general'),
    # Ruta para bloquear un producto especifico.
    path('productos/<int:product_id>/block/', views.producto_admin_block_view, name='producto_admin_block'),
    # Ruta para desbloquear un producto especifico.
    path('productos/<int:product_id>/unblock/', views.producto_admin_unblock_view, name='producto_admin_unblock'),
    # Ruta para generar reporte de usuarios.
    path('usuarios/reporte/', views.reporte_usuarios_view, name='reporte_usuarios'),
    # Ruta para crear un usuario desde admin.
    path('usuarios/crear/', views.usuario_admin_crear_view, name='usuario_admin_crear'),
    # Ruta para ver perfil del administrador.
    path('perfil/', views.admin_perfil_view, name='admin_perfil'),
    # Ruta para editar perfil del administrador.
    path('editar-perfil/', views.admin_editar_perfil_view, name='admin_editar_perfil'),
    # Ruta para crear un producto desde admin.
    path('productos/crear/', views.producto_admin_crear_view, name='producto_admin_crear'),
    # Ruta para editar un producto por ID.
    path('productos/<int:product_id>/editar/', views.producto_admin_editar_view, name='producto_admin_editar'),
    # Ruta para ver detalle de un producto por ID.
    path('productos/<int:product_id>/detalle/', views.producto_admin_detalle_view, name='producto_admin_detalle'),
    # Ruta para generar reporte de productos.
    path('productos/reporte/', views.reporte_productos_view, name='reporte_productos'),
    # Ruta para ver detalle de un pedido por ID.
    path('pedidos/<int:pedido_id>/', views.pedido_admin_detalle_view, name='pedido_admin_detalle'),
    # Ruta para editar un pedido por ID.
    path('pedidos/<int:pedido_id>/editar/', views.pedido_admin_editar_view, name='pedido_admin_editar'),
    # Ruta para generar reporte de pedidos.
    path('pedidos/reporte/', views.reporte_pedidos_view, name='reporte_pedidos'),
    # Ruta para ver listado de notificaciones de admin.
    path('notificaciones/', views.admin_notifications_view, name='admin_notifications'),
    # Ruta para marcar una notificacion como leida.
    path('notificaciones/<int:notification_id>/leer/', views.admin_notification_mark_read_view, name='admin_notification_mark_read'),
    # Ruta para desbloquear usuario desde una notificacion.
    path('notificaciones/<int:notification_id>/desbloquear/', views.admin_notification_unblock_user_view, name='admin_notification_unblock_user'),
    # Ruta para desbloquear producto desde una notificacion.
    path('notificaciones/<int:notification_id>/desbloquear-producto/', views.admin_notification_unblock_product_view, name='admin_notification_unblock_product'),
    # Ruta para responder una notificacion/mensaje desde admin.
    path('notificaciones/<int:notification_id>/responder/', views.admin_notification_reply_view, name='admin_notification_reply'),
]
