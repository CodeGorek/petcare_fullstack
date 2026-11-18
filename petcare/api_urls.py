from django.urls import include, path
from rest_framework.routers import DefaultRouter

from agenda.views import (
    CitaMedicaViewSet,
    FichaClinicaViewSet,
    RecordatorioVacunaViewSet,
    VeterinarioViewSet,
    api_disponibilidad_drf,
)
from cobros.views import CuentaAtencionViewSet, ServicioClinicoViewSet
from farmacia.views import LoteMedicamentoViewSet
from nucleo.views import api_metricas_drf, health_check
from pacientes.views import MascotaViewSet, TutorViewSet
from usuarios.views import NovedadPersonalViewSet, UsuarioViewSet, api_login, api_logout

router = DefaultRouter()
router.register(r'tutores', TutorViewSet)
router.register(r'mascotas', MascotaViewSet)
router.register(r'veterinarios', VeterinarioViewSet)
router.register(r'medicamentos-fefo', LoteMedicamentoViewSet)
router.register(r'citas', CitaMedicaViewSet)
router.register(r'fichas', FichaClinicaViewSet)
router.register(r'recordatorios', RecordatorioVacunaViewSet)
router.register(r'servicios', ServicioClinicoViewSet)
router.register(r'cuentas', CuentaAtencionViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'novedades-personal', NovedadPersonalViewSet)

urlpatterns = [
    path('health/', health_check, name='api_health'),
    path('auth/login/', api_login, name='api_login'),
    path('auth/logout/', api_logout, name='api_logout'),
    path('metricas/', api_metricas_drf, name='api_metricas_drf'),
    path('disponibilidad/', api_disponibilidad_drf, name='api_disponibilidad_drf'),
    path('', include(router.urls)),
]
