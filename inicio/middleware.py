"""Cabeceras HTTP de seguridad para todas las respuestas."""

CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
       "form-action 'self'; frame-ancestors 'none'")

# El sitio de administración de Django usa estilos en línea.
CSP_ADMIN = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
             "img-src 'self' data:; object-src 'none'; base-uri 'self'; "
             "form-action 'self'; frame-ancestors 'none'")

PERMISSIONS_POLICY = 'geolocation=(), camera=(), microphone=(), payment=(), usb=()'


class CabecerasSeguridadMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        es_admin = request.path.startswith('/admin/')
        response.headers['Content-Security-Policy'] = CSP_ADMIN if es_admin else CSP
        response.headers['Permissions-Policy'] = PERMISSIONS_POLICY
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Cabecera genérica: evita revelar el servidor y su versión
        response.headers['Server'] = 'ERP'
        if not request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'no-store'
        return response
