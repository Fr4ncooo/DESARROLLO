"""
URL configuration for DESARROLLO project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from inicio.autenticacion import LoginSeguroView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', LoginSeguroView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('inicio.urls')),
]

# Archivos estáticos del prototipo local: se sirven desde Django para que pasen por el middleware
# de cabeceras de seguridad. En producción los entrega el servidor web (nginx) o WhiteNoise.
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR / 'static')}),
]
