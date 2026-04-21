"""
URLs para la app de Purchasing.
"""
from django.urls import path
from apps.purchasing.views import (
    SugerenciasView,
    VencimientosView,
    PromocionesView,
    AnalisisABCView
)

urlpatterns = [
    path('compras/sugerencias/', SugerenciasView.as_view(), name='compras-sugerencias'),
    path('compras/vencimientos/', VencimientosView.as_view(), name='compras-vencimientos'),
    path('compras/promociones/', PromocionesView.as_view(), name='compras-promociones'),
    path('compras/abc/', AnalisisABCView.as_view(), name='compras-abc'),
]
