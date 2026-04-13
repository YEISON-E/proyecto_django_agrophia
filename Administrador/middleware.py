from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class AdminTwoFactorMiddleware:
    # Middleware de seguridad para el panel /administrador/.
    # Exige usuario autenticado, rol admin y validacion de codigo 2FA.
    """Enforces admin 2FA verification on all /administrador/ routes."""

    def __init__(self, get_response):
        # Referencia al siguiente middleware o vista en la cadena.
        self.get_response = get_response

    def __call__(self, request):
        # Ruta actual solicitada por el usuario.
        path = request.path or ""

        # Si no es una ruta del panel admin, no aplicamos este control.
        if not path.startswith("/administrador/"):
            return self.get_response(request)

        # Rutas permitidas sin exigir validacion admin ya confirmada.
        allowed_paths = {
            "/administrador/verificar-codigo/",
            "/administrador/logout/",
        }
        if path in allowed_paths:
            return self.get_response(request)

        # Si no hay sesion iniciada, guardamos destino y enviamos a login.
        if not request.user.is_authenticated:
            request.session["pending_admin_next"] = path
            messages.warning(request, "Debes iniciar sesion para continuar.")
            login_url = reverse("usuarios:login")
            return redirect(f"{login_url}?next={path}")

        # Import local para evitar ciclos y carga temprana innecesaria.
        from usuarios.models import Register

        # Verificamos que el usuario autenticado tenga perfil admin.
        register_admin = Register.objects.filter(id_usuario=request.user.id, estado="admin").first()
        if not register_admin:
            messages.error(request, "No tienes permisos para ingresar al panel administrativo.")
            return redirect("usuarios:home_customer")

        # El admin queda validado cuando:
        # 1) su bandera de codigo validado esta activa y
        # 2) la sesion corresponde al mismo usuario.
        is_validated = bool(
            register_admin.admin_code_validated
            and request.session.get("admin_user_id") == request.user.id
        )
        if not is_validated:
            # Permite continuar flujo de verificacion cuando el codigo ya fue
            # generado y sigue vigente en sesion para este usuario.
            has_pending_code = bool(
                request.session.get("pending_admin_user_id") == request.user.id
                and request.session.get("pending_admin_code")
                and request.session.get("pending_admin_code_expires_at")
            )

            if has_pending_code:
                # Guardamos de nuevo la ruta destino para volver despues de validar.
                request.session["pending_admin_next"] = path
                messages.warning(request, "Debes validar el codigo de seguridad para entrar al panel administrativo.")
                return redirect("administrador:admin_verify_code")

            # Si no hay codigo pendiente valido, cerramos sesion por seguridad.
            logout(request)
            request.session.flush()
            messages.warning(request, "Tu sesion de seguridad expiro. Inicia sesion nuevamente para generar un nuevo codigo.")
            return redirect("usuarios:login")

        # Si todo es valido, continuamos hacia la vista solicitada.
        return self.get_response(request)
