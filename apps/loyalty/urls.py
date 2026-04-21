"""
URLs para la app de Loyalty.
"""
from django.urls import path
from apps.loyalty.views import (
    ClienteLoyaltyView,
    AcumularPuntosView,
    CanjearPuntosView,
    TicketSoporteView,
    RankingView
)

urlpatterns = [
    path('loyalty/clientes/', ClienteLoyaltyView.as_view(), name='cliente-loyalty'),
    path('loyalty/clientes/<str:pk>/', ClienteLoyaltyView.as_view(), name='cliente-loyalty-detail'),
    path('loyalty/puntos/acumular/', AcumularPuntosView.as_view(), name='acumular-puntos'),
    path('loyalty/puntos/canjear/', CanjearPuntosView.as_view(), name='canjear-puntos'),
    path('loyalty/tickets/', TicketSoporteView.as_view(), name='ticket-soporte'),
    path('loyalty/ranking/', RankingView.as_view(), name='ranking-clientes'),
]
