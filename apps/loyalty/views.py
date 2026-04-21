"""
Views para la app de Loyalty.
Endpoints para clientes, puntos, tickets y ranking.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from apps.loyalty.services import (
    acumular_puntos,
    canjear_puntos,
    crear_ticket,
    get_cliente_info,
    get_ranking_clientes
)
from apps.core.audit import audit_log
from apps.core.errors import ErrorHandler


class ClienteLoyaltyView(APIView):
    """POST /api/v1/loyalty/clientes/ - Crea cliente loyalty"""
    
    @audit_log(action='CREAR_CLIENTE_LOYALTY')
    def post(self, request):
        try:
            from apps.loyalty.models import ClienteLoyalty
            
            nombre = request.data.get('nombre')
            if not nombre:
                raise ValueError("Nombre requerido")
            
            cliente = ClienteLoyalty.objects.create(
                nombre=nombre,
                puntos=0,
                nivel='BRONZE'
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": "Cliente creado",
                "data": {
                    "id": cliente.id,
                    "nombre": cliente.nombre,
                    "puntos": cliente.puntos,
                    "nivel": cliente.nivel
                },
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)
    
    def get(self, request, pk=None):
        """GET /api/v1/loyalty/clientes/{id}/"""
        try:
            data = get_cliente_info(pk)
            return Response({
                "success": True,
                "code": "OK",
                "message": "Cliente obtenido",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class AcumularPuntosView(APIView):
    """POST /api/v1/loyalty/puntos/acumular/"""
    
    @audit_log(action='ACUMULAR_PUNTOS')
    def post(self, request):
        try:
            id_cliente = request.data.get('id_cliente')
            monto_venta = request.data.get('monto_venta')
            
            if not id_cliente or not monto_venta:
                raise ValueError("id_cliente y monto_venta requeridos")
            
            resultado = acumular_puntos(
                id_cliente=id_cliente,
                monto_venta=float(monto_venta),
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": "Puntos acumulados",
                "data": resultado,
                "timestamp": datetime.utcnow().isoformat()
            })
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="INVALID_INPUT")
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class CanjearPuntosView(APIView):
    """POST /api/v1/loyalty/puntos/canjear/"""
    
    @audit_log(action='CANJEAR_PUNTOS')
    def post(self, request):
        try:
            id_cliente = request.data.get('id_cliente')
            puntos_a_canjear = request.data.get('puntos_a_canjear')
            
            if not id_cliente or not puntos_a_canjear:
                raise ValueError("id_cliente y puntos_a_canjear requeridos")
            
            resultado = canjear_puntos(
                id_cliente=id_cliente,
                puntos_a_canjear=int(puntos_a_canjear),
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": "Puntos canjeados",
                "data": resultado,
                "timestamp": datetime.utcnow().isoformat()
            })
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="INSUFFICIENT_POINTS")
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class TicketSoporteView(APIView):
    """POST /api/v1/loyalty/tickets/"""
    
    @audit_log(action='CREAR_TICKET')
    def post(self, request):
        try:
            cliente_id = request.data.get('cliente_id')
            asunto = request.data.get('asunto')
            descripcion = request.data.get('descripcion')
            
            if not all([cliente_id, asunto, descripcion]):
                raise ValueError("cliente_id, asunto y descripcion requeridos")
            
            resultado = crear_ticket(
                cliente_id=cliente_id,
                asunto=asunto,
                descripcion=descripcion,
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": "Ticket creado",
                "data": resultado,
                "timestamp": datetime.utcnow().isoformat()
            })
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="INVALID_INPUT")
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class RankingView(APIView):
    """GET /api/v1/loyalty/ranking/"""
    
    @audit_log(action='OBTENER_RANKING')
    def get(self, request):
        try:
            limite = int(request.query_params.get('limite', 10))
            data = get_ranking_clientes(limite)
            return Response({
                "success": True,
                "code": "OK",
                "message": "Ranking obtenido",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)
