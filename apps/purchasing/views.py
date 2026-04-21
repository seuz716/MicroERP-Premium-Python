"""
Views para la app de Purchasing.
Endpoints para sugerencias, vencimientos, promociones y análisis ABC.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from apps.purchasing.services import (
    sugerir_pedidos,
    get_vencimientos,
    get_promociones,
    analisis_abc
)
from apps.core.audit import audit_log
from apps.core.errors import ErrorHandler


class SugerenciasView(APIView):
    """GET /api/v1/compras/sugerencias/ - Sugiere pedidos basados en ventas"""
    
    @audit_log(action='OBTENER_SUGERENCIAS_PEDIDOS')
    def get(self, request):
        try:
            data = sugerir_pedidos()
            return Response({
                "success": True,
                "code": "OK",
                "message": "Sugerencias generadas",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class VencimientosView(APIView):
    """GET /api/v1/compras/vencimientos/ - Productos próximos a vencer"""
    
    @audit_log(action='OBTENER_VENCIMIENTOS')
    def get(self, request):
        try:
            data = get_vencimientos()
            return Response({
                "success": True,
                "code": "OK",
                "message": "Vencimientos obtenidos",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class PromocionesView(APIView):
    """GET /api/v1/compras/promociones/ - Productos para promocionar"""
    
    @audit_log(action='OBTENER_PROMOCIONES')
    def get(self, request):
        try:
            data = get_promociones()
            return Response({
                "success": True,
                "code": "OK",
                "message": "Promociones identificadas",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class AnalisisABCView(APIView):
    """GET /api/v1/compras/abc/ - Análisis ABC de productos"""
    
    @audit_log(action='OBTENER_ANALISIS_ABC')
    def get(self, request):
        try:
            data = analisis_abc()
            return Response({
                "success": True,
                "code": "OK",
                "message": "Análisis ABC obtenido",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)
