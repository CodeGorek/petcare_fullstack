from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from clinica import views as clinica_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('clinica.urls')),
    re_path(r'^(?P<ruta_invalida>.*)$', clinica_views.error_404_view),
]

handler404 = 'clinica.views.error_404_view'
handler403 = 'clinica.views.error_403_view'
