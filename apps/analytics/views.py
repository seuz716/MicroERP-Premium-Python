"""
Views para la app de Analytics.
Endpoints para estrellas, horarios, categorías y reportes.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from apps.analytics.services import (
    get_productos_estrella,
    get_horarios_pico,
    get_categorias_rentables,
    get_reporte_general
)
from apps.core.audit import audit_log
from apps.core.errors import ErrorHandler


class ProductosEstrellaView(APIView):
    """GET /api/v1/analytics/estrellas/ - Productos más rentables"""
    
    @audit_log(action='OBTENER_PRODUCTOS_ESTRELLA')
    def get(self, request):
        try:
            limite = int(request.query_params.get('limite', 10))
            data = get_productos_estrella(limite)
            return Response({
                "success": True,
                "code": "OK",
                "message": "Productos estrella obtenidos",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class HorariosPicoView(APIView):
    """GET /api/v1/analytics/horarios/ - Horarios de mayor venta"""
    
    @audit_log(action='OBTENER_HORARIOS_PICO')
    def get(self, request):
        try:
            data = get_horarios_pico()
            return Response({
                "success": True,
                "code": "OK",
                "message": "Horarios pico obtenidos",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class CategoriasRentablesView(APIView):
    """GET /api/v1/analytics/categorias/ - Categorías por rentabilidad"""
    
    @audit_log(action='OBTENER_CATEGORIAS_RENTABLES')
    def get(self, request):
        try:
            data = get_categorias_rentables()
            return Response({
                "success": True,
                "code": "OK",
                "message": "Categorías rentables obtenidas",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class ReporteGeneralView(APIView):
    """GET /api/v1/analytics/reporte/ - Reporte general de analytics"""
    
    @audit_log(action='OBTENER_REPORTE_GENERAL')
    def get(self, request):
        try:
            dias = int(request.query_params.get('dias', 30))
            data = get_reporte_general(dias)
            return Response({
                "success": True,
                "code": "OK",
                "message": "Reporte generado",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)
