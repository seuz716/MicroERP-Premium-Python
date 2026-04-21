#!/bin/bash
# Script para generar todas las APIs REST del MicroERP
echo "🚀 Generando APIs REST del MicroERP..."

# SALES - serializers.py
cat > /workspace/apps/sales/serializers.py << 'EOF'
from rest_framework import serializers
from apps.core.validators import Validators

class VentaProcesarSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField())
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Carrito vacío")
        for item in value:
            if 'producto_id' not in item and 'id' not in item:
                raise serializers.ValidationError("Cada item debe tener producto_id")
            if 'cantidad' not in item:
                raise serializers.ValidationError("Cada item debe tener cantidad")
        return value

class VentaReadSerializer(serializers.Serializer):
    id_venta = serializers.CharField()
    total = serializers.CharField()
    fecha = serializers.DateTimeField()
    items = serializers.IntegerField()

class DashboardSerializer(serializers.Serializer):
    ventas_hoy = serializers.IntegerField()
    monto_ventas_hoy = serializers.CharField()
    utilidad_hoy = serializers.CharField()
    stock_total = serializers.IntegerField()
    valor_inventario = serializers.CharField()
EOF

# SALES - views.py
cat > /workspace/apps/sales/views.py << 'EOF'
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from apps.sales.services import procesar_venta, get_historial_ventas, get_dashboard_kpis
from apps.sales.serializers import VentaProcesarSerializer
from apps.core.audit import audit_log
from apps.core.errors import ErrorHandler

class ProcesarVentaView(APIView):
    @audit_log(action='PROCESAR_VENTA')
    def post(self, request):
        try:
            serializer = VentaProcesarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = procesar_venta(
                cart_items=serializer.validated_data['items'],
                usuario=request.user if request.user.is_authenticated else None
            )
            return Response({
                "success": True, "code": "OK",
                "message": "Venta procesada exitosamente",
                "data": resultado,
                "timestamp": datetime.utcnow().isoformat()
            })
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="INSUFFICIENT_STOCK")
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class HistorialVentasView(APIView):
    @audit_log(action='CONSULTAR_HISTORIAL_VENTAS')
    def get(self, request):
        try:
            limite = int(request.query_params.get('limite', 50))
            data = get_historial_ventas(limite)
            return Response({
                "success": True, "code": "OK",
                "message": "Historial obtenido",
                "data": {"ventas": data},
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class DashboardView(APIView):
    @audit_log(action='CONSULTAR_DASHBOARD')
    def get(self, request):
        try:
            data = get_dashboard_kpis()
            return Response({
                "success": True, "code": "OK",
                "message": "KPIs obtenidos",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)
EOF

# SALES - urls.py
cat > /workspace/apps/sales/urls.py << 'EOF'
from django.urls import path
from apps.sales.views import ProcesarVentaView, HistorialVentasView, DashboardView

urlpatterns = [
    path('ventas/procesar/', ProcesarVentaView.as_view(), name='venta-procesar'),
    path('ventas/historial/', HistorialVentasView.as_view(), name='ventas-historial'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
EOF

echo "✅ Sales app completada"
