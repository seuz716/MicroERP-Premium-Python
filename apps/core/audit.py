"""
AuditLogger - Sistema de auditoría para MicroERP.
Registra todas las acciones importantes del sistema para trazabilidad.
"""
import logging
from typing import Optional, Dict, Any
from django.utils import timezone
from apps.core.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Logger de auditoría para registrar acciones del sistema.
    Uso: AuditLogger.log(action='CREATE_PRODUCT', details={...}, estado='SUCCESS')
    """
    
    @staticmethod
    def log(
        action: str,
        details: Dict[str, Any],
        estado: str = 'SUCCESS',
        usuario=None,
        ip_address: str = None,
        user_agent: str = None
    ) -> AuditLog:
        """
        Registra una acción en la base de datos de auditoría.
        
        Args:
            action: Nombre de la acción (ej: 'CREATE_PRODUCT', 'PROCESS_SALE')
            details: Diccionario con detalles de la acción
            estado: SUCCESS, ERROR o WARNING
            usuario: Usuario que realizó la acción (opcional)
            ip_address: IP del cliente (opcional)
            user_agent: User agent del cliente (opcional)
        
        Returns:
            Instancia de AuditLog creada
        """
        try:
            audit_entry = AuditLog.objects.create(
                accion=action,
                detalles=details,
                estado=estado,
                usuario=usuario,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # También loguear en el logger de Python
            log_message = f"AUDIT: {action} - {estado}"
            if estado == 'ERROR':
                logger.error(log_message, extra={'audit_details': details})
            elif estado == 'WARNING':
                logger.warning(log_message, extra={'audit_details': details})
            else:
                logger.info(log_message, extra={'audit_details': details})
            
            return audit_entry
            
        except Exception as e:
            logger.error(f"Error registrando auditoría: {str(e)}")
            # No lanzar excepción para no interrumpir el flujo principal
            return None
    
    @staticmethod
    def log_success(action: str, details: Dict[str, Any], **kwargs) -> AuditLog:
        """Registra una acción exitosa."""
        return AuditLogger.log(action=action, details=details, estado='SUCCESS', **kwargs)
    
    @staticmethod
    def log_error(action: str, details: Dict[str, Any], **kwargs) -> AuditLog:
        """Registra una acción fallida."""
        return AuditLogger.log(action=action, details=details, estado='ERROR', **kwargs)
    
    @staticmethod
    def log_warning(action: str, details: Dict[str, Any], **kwargs) -> AuditLog:
        """Registra una advertencia."""
        return AuditLogger.log(action=action, details=details, estado='WARNING', **kwargs)


def audit_log(action: str):
    """
    Decorador para auditar automáticamente la ejecución de una función.
    
    Uso:
        @audit_log('PROCESAR_VENTA')
        def procesar_venta(request, data):
            pass
    """
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Intentar obtener request y usuario de los argumentos
            request = None
            usuario = None
            ip_address = None
            user_agent = None
            
            for arg in args:
                if hasattr(arg, 'user'):
                    request = arg
                    usuario = arg.user if arg.user.is_authenticated else None
                    ip_address = getattr(arg, 'META', {}).get('REMOTE_ADDR')
                    user_agent = getattr(arg, 'META', {}).get('HTTP_USER_AGENT')
                    break
            
            try:
                # Ejecutar la función
                result = func(*args, **kwargs)
                
                # Registrar éxito
                AuditLogger.log_success(
                    action=action,
                    details={
                        'function': func.__name__,
                        'args': str(args)[:500],  # Limitar longitud
                        'kwargs': {k: v for k, v in kwargs.items() if k != 'request'},
                        'result': str(result)[:500] if result else None
                    },
                    usuario=usuario,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return result
                
            except Exception as e:
                # Registrar error
                AuditLogger.log_error(
                    action=action,
                    details={
                        'function': func.__name__,
                        'error': str(e),
                        'args': str(args)[:500]
                    },
                    usuario=usuario,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise
        
        return wrapper
    return decorator
