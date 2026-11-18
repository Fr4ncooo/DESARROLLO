"""Inicio de sesión con bloqueo temporal tras intentos fallidos (hallazgo H-08)."""
from django.contrib.auth.views import LoginView
from django.core.cache import cache

MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 15 * 60


class LoginSeguroView(LoginView):
    template_name = 'registration/login.html'

    def _clave(self, request):
        usuario = (request.POST.get('username') or '').strip().lower()[:150]
        ip = request.META.get('REMOTE_ADDR', '')
        return f'login_fallos:{usuario}:{ip}'

    def post(self, request, *args, **kwargs):
        if cache.get(self._clave(request), 0) >= MAX_INTENTOS:
            formulario = self.form_class(request=request)
            return self.render_to_response(
                self.get_context_data(form=formulario, bloqueado=True), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        clave = self._clave(self.request)
        cache.add(clave, 0, BLOQUEO_SEGUNDOS)
        try:
            cache.incr(clave)
        except ValueError:
            cache.set(clave, 1, BLOQUEO_SEGUNDOS)
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(self._clave(self.request))
        return super().form_valid(form)
