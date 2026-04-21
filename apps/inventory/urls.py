"""
URLs para la app de Inventario.
"""
from django.urls import path
from apps.inventory.views import (
    ProductoListCreateView,
    ProductoDetailView,
    EntradaView
)

urlpatterns = [
    path('productos/', ProductoListCreateView.as_view(), name='producto-list-create'),
    path('productos/<str:pk>/', ProductoDetailView.as_view(), name='producto-detail'),
    path('entradas/', EntradaView.as_view(), name='entrada-registrar'),
]
