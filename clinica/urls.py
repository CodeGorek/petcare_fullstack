from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tutores', views.TutorViewSet)
router.register(r'mascotas', views.MascotaViewSet)
router.register(r'veterinarios', views.VeterinarioViewSet)
router.register(r'citas', views.CitaMedicaViewSet)
router.register(r'fichas', views.FichaClinicaViewSet)
router.register(r'recordatorios', views.RecordatorioVacunaViewSet)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tutores-mascotas/', views.gestion_tutores_mascotas, name='tutores_mascotas'),
    path('mascotas/<int:pk>/editar/', views.editar_mascota, name='editar_mascota'),
    path('mascotas/<int:pk>/eliminar/', views.eliminar_mascota, name='eliminar_mascota'),
    path('agenda/', views.agenda_citas, name='agenda_citas'),
    path('agenda/<int:pk>/estado/<str:nuevo_estado>/', views.cambiar_estado_cita, name='cambiar_estado_cita'),
    path('agenda/disponibilidad/', views.api_disponibilidad_veterinario, name='api_disponibilidad'),
    path('fichas/', views.fichas_clinicas, name='fichas_clinicas'),
    path('recordatorios/', views.recordatorios_vacunas, name='recordatorios_vacunas'),
    path('recordatorios/<int:pk>/aplicar/', views.marcar_recordatorio_aplicado, name='marcar_recordatorio_aplicado'),
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('api/', include(router.urls)),
]
