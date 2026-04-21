"""
URLs para la app de Analytics.
"""
from django.urls import path
from apps.analytics.views import (
    ProductosEstrellaView,
    HorariosPicoView,
    CategoriasRentablesView,
    ReporteGeneralView
)

urlpatterns = [
    path('analytics/estrellas/', ProductosEstrellaView.as_view(), name='analytics-estrellas'),
    path('analytics/horarios/', HorariosPicoView.as_view(), name='analytics-horarios'),
    path('analytics/categorias/', CategoriasRentablesView.as_view(), name='analytics-categorias'),
    path('analytics/reporte/', ReporteGeneralView.as_view(), name='analytics-reporte'),
]
