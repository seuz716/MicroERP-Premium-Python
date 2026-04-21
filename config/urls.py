"""
Configuración principal de Django para MicroERP.
Este archivo define la URL raíz del proyecto.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # API REST versión 1
    path('api/v1/inventory/', include('apps.inventory.urls')),
    path('api/v1/sales/', include('apps.sales.urls')),
    path('api/v1/cartera/', include('apps.cartera.urls')),
    path('api/v1/finance/', include('apps.finance.urls')),
    path('api/v1/compras/', include('apps.purchasing.urls')),
    path('api/v1/loyalty/', include('apps.loyalty.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Títulos del admin
admin.site.site_header = "MicroERP Administration"
admin.site.site_title = "MicroERP Admin"
admin.site.index_title = "Panel de Control"
