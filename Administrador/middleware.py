from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class AdminTwoFactorMiddleware:
    """Enforces admin 2FA verification on all /administrador/ routes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or ""

        if not path.startswith("/administrador/"):
            return self.get_response(request)

        allowed_paths = {
            "/administrador/verificar-codigo/",
            "/administrador/logout/",
        }
        if path in allowed_paths:
            return self.get_response(request)

        if not request.user.is_authenticated:
            request.session["pending_admin_next"] = path
            messages.warning(request, "Debes iniciar sesion para continuar.")
            login_url = reverse("usuarios:login")
            return redirect(f"{login_url}?next={path}")

        from usuarios.models import Register

        register_admin = Register.objects.filter(id_usuario=request.user.id, estado="admin").first()
        if not register_admin:
            messages.error(request, "No tienes permisos para ingresar al panel administrativo.")
            return redirect("usuarios:home_customer")

        is_validated = bool(
            register_admin.admin_code_validated
            and request.session.get("admin_user_id") == request.user.id
        )
        if not is_validated:
            has_pending_code = bool(
                request.session.get("pending_admin_user_id") == request.user.id
                and request.session.get("pending_admin_code")
                and request.session.get("pending_admin_code_expires_at")
            )

            if has_pending_code:
                request.session["pending_admin_next"] = path
                messages.warning(request, "Debes validar el codigo de seguridad para entrar al panel administrativo.")
                return redirect("administrador:admin_verify_code")

            logout(request)
            request.session.flush()
            messages.warning(request, "Tu sesion de seguridad expiro. Inicia sesion nuevamente para generar un nuevo codigo.")
            return redirect("usuarios:login")

        return self.get_response(request)
