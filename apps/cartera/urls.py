from django.urls import path
from apps.cartera.views import ClienteCreditoView, FacturaView, PagoView, CarteraStatusView

urlpatterns = [
    path('cartera/clientes/', ClienteCreditoView.as_view(), name='cliente-credito'),
    path('cartera/clientes/<str:pk>/', ClienteCreditoView.as_view(), name='cliente-credito-detail'),
    path('cartera/facturas/', FacturaView.as_view(), name='factura'),
    path('cartera/pagos/', PagoView.as_view(), name='pago'),
    path('cartera/status/', CarteraStatusView.as_view(), name='cartera-status'),
]
