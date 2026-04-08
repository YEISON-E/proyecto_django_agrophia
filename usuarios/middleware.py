import os
from django.conf import settings


class RegisterFlowCleanupMiddleware:
    """Limpia datos temporales del registro al salir del flujo /usuarios/register/."""

    REGISTER_SESSION_KEYS = ("register_step_1", "register_step_2", "foto_temp_path")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip("/")
        in_register_flow = path == "/usuarios/register" or path.startswith("/usuarios/register/")
        static_prefix = "/" + settings.STATIC_URL.lstrip("/")
        media_prefix = "/" + settings.MEDIA_URL.lstrip("/")
        is_asset_request = request.path.startswith(static_prefix) or request.path.startswith(media_prefix)
        is_document_request = request.method == "GET" and request.headers.get("Sec-Fetch-Dest", "") in ("", "document")

        if is_document_request and not is_asset_request and not in_register_flow and any(key in request.session for key in self.REGISTER_SESSION_KEYS):
            temp_path = request.session.get("foto_temp_path")
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

            for key in self.REGISTER_SESSION_KEYS:
                request.session.pop(key, None)

        response = self.get_response(request)
        return response
