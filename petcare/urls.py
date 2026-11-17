from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path

from nucleo import views as nucleo_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/', include('petcare.api_urls')),
    path('', include('nucleo.urls')),
    path('', include('usuarios.urls')),
    path('', include('pacientes.urls')),
    path('', include('agenda.urls')),
    path('', include('farmacia.urls')),
    path('', include('cobros.urls')),
    re_path(r'^(?P<ruta_invalida>.*)$', nucleo_views.error_404_view),
]

handler404 = 'nucleo.views.error_404_view'
handler403 = 'nucleo.views.error_403_view'
