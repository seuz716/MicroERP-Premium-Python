from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from apps.finance.services import (
    registrar_movimiento, registrar_fiado, registrar_pago_fiado,
    registrar_pago_digital, get_flujo_caja, get_fiados_proximos_vencer
)
from apps.finance.serializers import (
    MovimientoSerializer, FiadoSerializer, PagoFiadoSerializer, PagoDigitalSerializer
)
from apps.core.audit import audit_log
from apps.core.errors import ErrorHandler

class MovimientoView(APIView):
    @audit_log(action='REGISTRAR_MOVIMIENTO')
    def post(self, request):
        try:
            serializer = MovimientoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = registrar_movimiento(**serializer.validated_data, usuario=request.user if request.user.is_authenticated else None)
            return Response({"success": True, "code": "OK", "message": "Movimiento registrado", "data": resultado, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class FiadoView(APIView):
    @audit_log(action='REGISTRAR_FIADO')
    def post(self, request):
        try:
            serializer = FiadoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = registrar_fiado(**serializer.validated_data, usuario=request.user if request.user.is_authenticated else None)
            return Response({"success": True, "code": "OK", "message": "Fiado registrado", "data": resultado, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class PagoFiadoView(APIView):
    @audit_log(action='REGISTRAR_PAGO_FIADO')
    def post(self, request, pk):
        try:
            serializer = PagoFiadoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = registrar_pago_fiado(pk, serializer.validated_data['monto'], serializer.validated_data['metodo'], request.user if request.user.is_authenticated else None)
            return Response({"success": True, "code": "OK", "message": "Pago fiado registrado", "data": resultado, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class PagoDigitalView(APIView):
    @audit_log(action='REGISTRAR_PAGO_DIGITAL')
    def post(self, request):
        try:
            serializer = PagoDigitalSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            resultado = registrar_pago_digital(**serializer.validated_data, usuario=request.user if request.user.is_authenticated else None)
            return Response({"success": True, "code": "OK", "message": "Pago digital registrado", "data": resultado, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class FlujoCajaView(APIView):
    @audit_log(action='CONSULTAR_FLUJO_CAJA')
    def get(self, request):
        try:
            dias = int(request.query_params.get('dias', 30))
            data = get_flujo_caja(dias)
            return Response({"success": True, "code": "OK", "message": "Flujo de caja obtenido", "data": data, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)

class FiadosVencerView(APIView):
    @audit_log(action='CONSULTAR_FIADOS_VENCER')
    def get(self, request):
        try:
            data = get_fiados_proximos_vencer()
            return Response({"success": True, "code": "OK", "message": "Fiados próximos a vencer", "data": data, "timestamp": datetime.utcnow().isoformat()})
        except Exception as e:
            return ErrorHandler.handle_exception(e)
