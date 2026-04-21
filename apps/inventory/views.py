"""
Views para la app de Inventario.
Las views solo orquestan, los services ejecutan la lógica.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from apps.inventory.services import (
    get_productos_cached,
    crear_producto,
    actualizar_producto,
    eliminar_producto,
    registrar_entrada
)
from apps.inventory.serializers import (
    ProductoWriteSerializer,
    EntradaWriteSerializer
)
from apps.core.audit import audit_log
from apps.core.errors import ErrorHandler


class ProductoListCreateView(APIView):
    """GET /api/v1/productos/ - POST /api/v1/productos/"""
    
    @audit_log(action='LISTAR_PRODUCTOS')
    def get(self, request):
        try:
            productos = get_productos_cached()
            return Response({
                "success": True,
                "code": "OK",
                "message": "Productos obtenidos exitosamente",
                "data": {"productos": productos},
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e)

    @audit_log(action='CREAR_PRODUCTO')
    def post(self, request):
        try:
            serializer = ProductoWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            resultado = crear_producto(
                datos=serializer.validated_data,
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": "Producto creado exitosamente",
                "data": resultado,
                "timestamp": datetime.utcnow().isoformat()
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="INVALID_INPUT")
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class ProductoDetailView(APIView):
    """PUT /api/v1/productos/{id}/ - DELETE /api/v1/productos/{id}/"""
    
    @audit_log(action='ACTUALIZAR_PRODUCTO')
    def put(self, request, pk):
        try:
            serializer = ProductoWriteSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            resultado = actualizar_producto(
                producto_id=pk,
                datos=serializer.validated_data,
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": "Producto actualizado exitosamente",
                "data": resultado,
                "timestamp": datetime.utcnow().isoformat()
            })
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="NOT_FOUND")
        except Exception as e:
            return ErrorHandler.handle_exception(e)

    @audit_log(action='ELIMINAR_PRODUCTO')
    def delete(self, request, pk):
        try:
            resultado = eliminar_producto(
                producto_id=pk,
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": resultado.get('mensaje', 'Producto eliminado'),
                "data": None,
                "timestamp": datetime.utcnow().isoformat()
            })
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="NOT_FOUND")
        except Exception as e:
            return ErrorHandler.handle_exception(e)


class EntradaView(APIView):
    """POST /api/v1/entradas/"""
    
    @audit_log(action='REGISTRAR_ENTRADA')
    def post(self, request):
        try:
            serializer = EntradaWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            resultado = registrar_entrada(
                producto_id=serializer.validated_data['producto_id'],
                cantidad=serializer.validated_data['cantidad'],
                costo=serializer.validated_data['costo'],
                usuario=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                "success": True,
                "code": "OK",
                "message": "Entrada registrada exitosamente",
                "data": resultado,
                "timestamp": datetime.utcnow().isoformat()
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return ErrorHandler.handle_exception(e, code="NOT_FOUND")
        except Exception as e:
            return ErrorHandler.handle_exception(e)
