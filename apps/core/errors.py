"""
ErrorHandler - Manejador de errores estandarizado para MicroERP.
Todas las respuestas de error siguen el formato: {success, code, message, data, timestamp}
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError, NotFound, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ErrorResponse(APIException):
    """
    Excepción personalizada para errores del negocio.
    Uso: raise ErrorResponse(code='INSUFFICIENT_STOCK', message='No hay stock suficiente')
    """
    
    def __init__(self, code: str, message: str, status_code: int = 400, data: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(detail=message)
    
    def get_response(self) -> dict:
        """Retorna la respuesta estandarizada."""
        return format_error_response(
            code=self.code,
            message=self.message,
            data=self.data,
            status_code=self.status_code
        )


# Códigos de error estándar del sistema
ERROR_CODES = {
    'OK': ('Operación exitosa', 200),
    'INVALID_INPUT': ('Datos de entrada inválidos', 400),
    'NOT_FOUND': ('Recurso no encontrado', 404),
    'INSUFFICIENT_STOCK': ('Stock insuficiente', 400),
    'LOCK_TIMEOUT': ('Timeout adquiriendo lock', 408),
    'DB_ERROR': ('Error de base de datos', 500),
    'PERMISSION_DENIED': ('Permiso denegado', 403),
    'UNAUTHORIZED': ('No autorizado', 401),
    'DUPLICATE_ENTRY': ('Registro duplicado', 409),
    'BUSINESS_RULE_VIOLATION': ('Violación de regla de negocio', 400),
    'EXTERNAL_SERVICE_ERROR': ('Error en servicio externo', 502),
    'VALIDATION_ERROR': ('Error de validación', 400),
}


def format_error_response(code: str, message: str = None, data: dict = None, status_code: int = None) -> dict:
    """
    Formatea una respuesta de error estandarizada.
    
    Args:
        code: Código de error (ej: 'INVALID_INPUT')
        message: Mensaje descriptivo (opcional, usa el default si no se proporciona)
        data: Datos adicionales (opcional)
        status_code: Código HTTP (opcional, usa el default si no se proporciona)
    
    Returns:
        Diccionario con formato: {success, code, message, data, timestamp}
    """
    if code not in ERROR_CODES:
        logger.warning(f"Código de error desconocido: {code}")
        default_msg, default_status = ERROR_CODES['DB_ERROR']
    else:
        default_msg, default_status = ERROR_CODES[code]
    
    return {
        'success': False,
        'code': code,
        'message': message or default_msg,
        'data': data or {},
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def format_success_response(data: dict = None, message: str = 'OK') -> dict:
    """
    Formatea una respuesta de éxito estandarizada.
    
    Args:
        data: Datos de la respuesta
        message: Mensaje opcional
    
    Returns:
        Diccionario con formato: {success, code, message, data, timestamp}
    """
    return {
        'success': True,
        'code': 'OK',
        'message': message,
        'data': data or {},
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def custom_exception_handler(exc, context):
    """
    Manejador personalizado de excepciones para DRF.
    Intercepta todas las excepciones y las convierte al formato estándar.
    """
    # Llamar al manejador por defecto de DRF primero
    response = exception_handler(exc, context)
    
    # Si DRF ya manejó la excepción, convertir al formato estándar
    if response is not None:
        # Determinar código de error basado en el tipo de excepción
        if isinstance(exc, ErrorResponse):
            code = exc.code
            message = exc.message
            data = exc.data
        elif isinstance(exc, ValidationError):
            code = 'VALIDATION_ERROR'
            message = 'Error de validación en los datos enviados'
            data = {'details': response.data}
        elif isinstance(exc, NotFound) or isinstance(exc, Http404):
            code = 'NOT_FOUND'
            message = 'Recurso no encontrado'
            data = {}
        elif isinstance(exc, PermissionDenied):
            code = 'PERMISSION_DENIED'
            message = 'No tiene permisos para realizar esta acción'
            data = {}
        else:
            code = 'DB_ERROR' if response.status_code >= 500 else 'INVALID_INPUT'
            message = response.data.get('detail', str(exc)) if isinstance(response.data, dict) else str(response.data)
            data = {}
        
        # Construir respuesta estandarizada
        response.data = format_error_response(
            code=code,
            message=message,
            data=data,
            status_code=response.status_code
        )
        
        return response
    
    # Manejar excepciones no procesadas por DRF
    if isinstance(exc, ErrorResponse):
        from rest_framework.response import Response
        return Response(
            exc.get_response(),
            status=exc.status_code
        )
    
    # Loggear excepción no manejada
    logger.error(f"Excepción no manejada: {str(exc)}", exc_info=True)
    
    # Retornar error genérico
    from rest_framework.response import Response
    return Response(
        format_error_response(
            code='DB_ERROR',
            message='Error interno del servidor',
            data={'error_type': type(exc).__name__},
            status_code=500
        ),
        status=500
    )
