"""
URLs principales del MicroERP.
Todas las rutas bajo /api/v1/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include([
        # Inventory
        path('', include('apps.inventory.urls')),
        # Sales
        path('', include('apps.sales.urls')),
        # Cartera
        path('', include('apps.cartera.urls')),
        # Finance
        path('', include('apps.finance.urls')),
        # Purchasing
        path('', include('apps.purchasing.urls')),
        # Loyalty
        path('', include('apps.loyalty.urls')),
        # Analytics
        path('', include('apps.analytics.urls')),
    ])),
]
