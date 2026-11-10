from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tutores', views.TutorViewSet)
router.register(r'mascotas', views.MascotaViewSet)
router.register(r'veterinarios', views.VeterinarioViewSet)
router.register(r'medicamentos-fefo', views.LoteMedicamentoViewSet)
router.register(r'citas', views.CitaMedicaViewSet)
router.register(r'fichas', views.FichaClinicaViewSet)
router.register(r'recordatorios', views.RecordatorioVacunaViewSet)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('metricas-json/', views.api_metricas_dashboard, name='api_metricas_dashboard'),
    path('tutores-mascotas/', views.gestion_tutores_mascotas, name='tutores_mascotas'),
    path('tutores/<int:pk>/editar/', views.editar_tutor, name='editar_tutor'),
    path('tutores/<int:pk>/estado/', views.toggle_estado_tutor, name='toggle_estado_tutor'),
    path('mascotas/<int:pk>/expediente/', views.expediente_mascota, name='expediente_mascota'),
    path('mascotas/<int:pk>/editar/', views.editar_mascota, name='editar_mascota'),
    path('mascotas/<int:pk>/estado/', views.toggle_estado_mascota, name='toggle_estado_mascota'),
    path('agenda/', views.agenda_citas, name='agenda_citas'),
    path('agenda/<int:pk>/editar/', views.editar_cita, name='editar_cita'),
    path('agenda/<int:pk>/estado/<str:nuevo_estado>/', views.cambiar_estado_cita, name='cambiar_estado_cita'),
    path('agenda/disponibilidad/', views.api_disponibilidad_veterinario, name='api_disponibilidad'),
    path('fichas/', views.fichas_clinicas, name='fichas_clinicas'),
    path('fichas/<int:pk>/imprimir/', views.imprimir_ficha_individual, name='imprimir_ficha_individual'),
    path('farmacia-fefo/', views.farmacia_fefo, name='farmacia_fefo'),
    path('farmacia-fefo/<int:pk>/stock/<str:accion>/', views.ajustar_stock_lote, name='ajustar_stock_lote'),
    path('recordatorios/', views.recordatorios_vacunas, name='recordatorios_vacunas'),
    path('recordatorios/<int:pk>/asistencia/<str:resultado>/', views.actualizar_asistencia_recordatorio, name='actualizar_asistencia_recordatorio'),
    path('usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('api/', include(router.urls)),
]
