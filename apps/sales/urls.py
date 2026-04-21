from django.urls import path
from apps.sales.views import ProcesarVentaView, HistorialVentasView, DashboardView

urlpatterns = [
    path('ventas/procesar/', ProcesarVentaView.as_view(), name='venta-procesar'),
    path('ventas/historial/', HistorialVentasView.as_view(), name='ventas-historial'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
