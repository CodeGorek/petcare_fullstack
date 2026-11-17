from django.urls import path
from . import views

urlpatterns = [
    path('agenda/', views.agenda_citas, name='agenda_citas'),
    path('agenda/<int:pk>/editar/', views.editar_cita, name='editar_cita'),
    path('agenda/<int:pk>/estado/<str:nuevo_estado>/', views.cambiar_estado_cita, name='cambiar_estado_cita'),
    path('agenda/disponibilidad/', views.api_disponibilidad_veterinario, name='api_disponibilidad'),
    path('fichas/', views.fichas_clinicas, name='fichas_clinicas'),
    path('fichas/<int:pk>/imprimir/', views.imprimir_ficha_individual, name='imprimir_ficha_individual'),
    path('recordatorios/', views.recordatorios_vacunas, name='recordatorios_vacunas'),
    path('recordatorios/<int:pk>/asistencia/<str:resultado>/', views.actualizar_asistencia_recordatorio, name='actualizar_asistencia_recordatorio'),
]
