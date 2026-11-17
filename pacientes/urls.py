from django.urls import path
from . import views

urlpatterns = [
    path('tutores-mascotas/', views.gestion_tutores_mascotas, name='tutores_mascotas'),
    path('tutores/<int:pk>/editar/', views.editar_tutor, name='editar_tutor'),
    path('tutores/<int:pk>/estado/', views.toggle_estado_tutor, name='toggle_estado_tutor'),
    path('mascotas/<int:pk>/expediente/', views.expediente_mascota, name='expediente_mascota'),
    path('mascotas/<int:pk>/editar/', views.editar_mascota, name='editar_mascota'),
    path('mascotas/<int:pk>/estado/', views.toggle_estado_mascota, name='toggle_estado_mascota'),
]
