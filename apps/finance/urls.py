from django.urls import path
from apps.finance.views import (
    MovimientoView, FiadoView, PagoFiadoView, PagoDigitalView, FlujoCajaView, FiadosVencerView
)

urlpatterns = [
    path('finance/movimientos/', MovimientoView.as_view(), name='movimiento'),
    path('finance/fiados/', FiadoView.as_view(), name='fiado'),
    path('finance/fiados/<str:pk>/pagar/', PagoFiadoView.as_view(), name='pago-fiado'),
    path('finance/pagos-digitales/', PagoDigitalView.as_view(), name='pago-digital'),
    path('finance/flujo-caja/', FlujoCajaView.as_view(), name='flujo-caja'),
    path('finance/fiados/vencer/', FiadosVencerView.as_view(), name='fiados-vencer'),
]
