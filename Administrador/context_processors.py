def admin_nav_context(request):
    if not request.user.is_authenticated:
        return {
            "admin_unread_notifications_count": 0,
            "admin_display_name": "Administrador",
            "admin_display_email": "admin@correo.com",
        }

    try:
        from usuarios.models import Register
        from Mensajes.models import AdminNotification

        register_admin = Register.objects.filter(id_usuario=request.user.id, estado='admin').first()
        if not register_admin:
            fallback_name = (request.user.get_full_name() or "Administrador").strip()
            fallback_email = (request.user.email or "admin@correo.com").strip()
            return {
                "admin_unread_notifications_count": 0,
                "admin_display_name": fallback_name,
                "admin_display_email": fallback_email,
            }

        unread_count = AdminNotification.objects.filter(is_read=False).exclude(
            notification_type=AdminNotification.TYPE_BLOCKED_LOGIN_ATTEMPT,
            message__startswith='El usuario bloqueado intento iniciar sesion.'
        ).count()
        full_name = f"{register_admin.nombres} {register_admin.apellidos}".strip()
        display_name = full_name or (request.user.get_full_name() or "Administrador").strip()
        display_email = (register_admin.correo_electronico or request.user.email or "admin@correo.com").strip()
        return {
            "admin_unread_notifications_count": unread_count,
            "admin_display_name": display_name,
            "admin_display_email": display_email,
        }
    except Exception:
        # During migrations or startup, fail safe with zero notifications.
        fallback_name = "Administrador"
        fallback_email = "admin@correo.com"
        if request.user.is_authenticated:
            fallback_name = (request.user.get_full_name() or fallback_name).strip()
            fallback_email = (request.user.email or fallback_email).strip()
        return {
            "admin_unread_notifications_count": 0,
            "admin_display_name": fallback_name,
            "admin_display_email": fallback_email,
        }
