from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('metricas-json/', views.api_metricas_dashboard, name='api_metricas_dashboard'),
]
