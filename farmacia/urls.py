from django.urls import path
from . import views

urlpatterns = [
    path('farmacia-fefo/', views.farmacia_fefo, name='farmacia_fefo'),
    path('farmacia-fefo/<int:pk>/stock/<str:accion>/', views.ajustar_stock_lote, name='ajustar_stock_lote'),
]
