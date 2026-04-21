from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from apps.cartera.services import (
    crear_cliente_credito, registrar_factura, registrar_pago, get_cartera_status
)
from apps.cartera.serializers import ClienteCreditoSerializer, FacturaSerializer, PagoSerializer
from apps.core.audit import audit_log
from apps.core.errors import ErrorHandler

class ClienteCreditoView(APIView):
    @audit_log(action='CREAR_CLIENTE_CREDITO')
    def post(self, request):
        try:
            serializer = ClienteCreditoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = crear_cliente_credito(
                serializer.validated_data['nombre'],
                serializer.validated_data['limite_credito'],
                request.user if request.user.is_authenticated else None
            )
            return Response({"success": True, "code": "OK", "message": "Cliente creado", "data": resultado, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)
    
    def delete(self, request, pk):
        from apps.cartera.models import ClienteCredito
        try:
            ClienteCredito.objects.filter(id=pk).update(activo=False)
            return Response({"success": True, "code": "OK", "message": "Cliente eliminado", "data": None, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class FacturaView(APIView):
    @audit_log(action='REGISTRAR_FACTURA')
    def post(self, request):
        try:
            serializer = FacturaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = registrar_factura(
                serializer.validated_data['id_cliente'],
                serializer.validated_data['items'],
                serializer.validated_data['fecha_vencimiento'],
                request.user if request.user.is_authenticated else None
            )
            return Response({"success": True, "code": "OK", "message": "Factura registrada", "data": resultado, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class PagoView(APIView):
    @audit_log(action='REGISTRAR_PAGO')
    def post(self, request):
        try:
            serializer = PagoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = registrar_pago(
                serializer.validated_data['id_factura'],
                serializer.validated_data['monto'],
                request.user if request.user.is_authenticated else None
            )
            return Response({"success": True, "code": "OK", "message": "Pago registrado", "data": resultado, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class CarteraStatusView(APIView):
    @audit_log(action='CONSULTAR_CARTERA_STATUS')
    def get(self, request):
        try:
            data = get_cartera_status()
            return Response({"success": True, "code": "OK", "message": "Status obtenido", "data": data, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)
