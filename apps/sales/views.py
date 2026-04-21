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
