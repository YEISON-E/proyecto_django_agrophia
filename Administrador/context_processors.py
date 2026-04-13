# Context processor del panel admin.
# Su objetivo es inyectar datos globales para la barra superior:
# - Cantidad de notificaciones no leidas
# - Nombre a mostrar del administrador
# - Correo a mostrar del administrador
def admin_nav_context(request):
    # Si no hay sesion autenticada, devolvemos valores por defecto.
    if not request.user.is_authenticated:
        return {
            "admin_unread_notifications_count": 0,
            "admin_display_name": "Administrador",
            "admin_display_email": "admin@correo.com",
        }

    try:
        # Importes locales para evitar problemas durante arranque/migraciones.
        from usuarios.models import Register
        from Mensajes.models import AdminNotification

        # Buscamos el perfil Register del usuario autenticado con rol admin.
        register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()

        # Si no existe perfil admin asociado, usamos datos fallback del usuario auth.
        if not register_admin:
            fallback_name = (request.user.get_full_name() or "Administrador").strip()
            fallback_email = (request.user.email or "admin@correo.com").strip()
            return {
                "admin_unread_notifications_count": 0,
                "admin_display_name": fallback_name,
                "admin_display_email": fallback_email,
            }

        # Contamos notificaciones no leidas, excluyendo el caso especial de
        # bloqueo por intento de login que no queremos mostrar en el badge.
        unread_count = AdminNotification.objects.filter(is_read=False).exclude(
            notification_type=AdminNotification.TYPE_BLOCKED_LOGIN_ATTEMPT,
            message__startswith='El usuario bloqueado intento iniciar sesion.'
        ).count()

        # Definimos nombre/correo a mostrar priorizando datos del Register admin.
        full_name = f"{register_admin.nombres} {register_admin.apellidos}".strip()
        display_name = full_name or (request.user.get_full_name() or "Administrador").strip()
        display_email = (register_admin.correo_electronico or request.user.email or "admin@correo.com").strip()

        # Retornamos el contexto global que consumen los templates admin.
        return {
            "admin_unread_notifications_count": unread_count,
            "admin_display_name": display_name,
            "admin_display_email": display_email,
        }
    except Exception:
        # Fallback de seguridad: si algo falla (migraciones, DB no lista, etc.)
        # evitamos romper el render y enviamos valores seguros.
        fallback_name = "Administrador"
        fallback_email = "admin@correo.com"

        # Si aun hay usuario autenticado, intentamos tomar su nombre/correo.
        if request.user.is_authenticated:
            fallback_name = (request.user.get_full_name() or fallback_name).strip()
            fallback_email = (request.user.email or fallback_email).strip()

        # Contexto minimo seguro para que el navbar admin siga funcionando.
        return {
            "admin_unread_notifications_count": 0,
            "admin_display_name": fallback_name,
            "admin_display_email": fallback_email,
        }
