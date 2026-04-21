"""
LockManager - Sistema de locks distribuidos con Redis.
Previene race conditions en operaciones críticas como descuento de stock.
Implementa retry con exponential backoff y detección de phantom locks.
"""
import time
import uuid
import logging
from functools import wraps
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LockManager:
    """
    Gestiona locks distribuidos usando Redis.
    Patrón: RedLock con exponential backoff.
    """
    
    DEFAULT_TIMEOUT = 15  # segundos
    DEFAULT_RETRIES = 3
    BACKOFF_BASE = 0.5  # 500ms base para exponential backoff
    MAX_BACKOFF = 5.0  # límite máximo para evitar esperas excesivas
    
    @classmethod
    def cleanup_phantom_locks(cls, key_pattern: str = 'lock:*', max_age_seconds: int = 45):
        """
        Detecta y libera locks fantasma (existentes >45s).
        Debe ejecutarse periódicamente (ej: cada 5 minutos) vía Celery Beat.
        """
        try:
            from django.core.cache import caches
            redis_client = caches['default'].client.get_client()
            phantom_count = 0
            
            for key in redis_client.keys(key_pattern):
                ttl = redis_client.ttl(key)
                # TTL -1 significa sin expiración, o TTL > max_age_seconds indica lock antiguo
                if ttl == -1 or ttl > max_age_seconds:
                    logger.warning(f"Phantom lock detectado: {key}, TTL: {ttl}s")
                    redis_client.delete(key)
                    phantom_count += 1
            
            if phantom_count > 0:
                logger.info(f"Se limpiaron {phantom_count} phantom locks")
            
            return phantom_count
        except Exception as e:
            logger.error(f"Error limpiando phantom locks: {e}")
            return 0
    
    @classmethod
    def acquire(cls, key: str, timeout: int = None, token: str = None) -> bool:
        """
        Adquiere un lock con un token único.
        Usa SET NX EX para atomicidad.
        """
        timeout = timeout or cls.DEFAULT_TIMEOUT
        token = token or str(uuid.uuid4())
        
        # Intentar adquirir el lock
        acquired = cache.set(key, token, timeout, nx=True)
        
        if acquired:
            logger.debug(f"Lock adquirido: {key} (token: {token[:8]}...)")
            return True
        
        logger.debug(f"Lock no disponible: {key}")
        return False
    
    @classmethod
    def release(cls, key: str, token: str) -> bool:
        """
        Libera un lock solo si el token coincide.
        Previene que un proceso libere el lock de otro.
        """
        # Verificar que el token coincide antes de liberar
        current_token = cache.get(key)
        
        if current_token == token:
            cache.delete(key)
            logger.debug(f"Lock liberado: {key} (token: {token[:8]}...)")
            return True
        
        logger.warning(f"Intento de liberar lock con token incorrecto: {key}")
        return False
    
    @classmethod
    def is_locked(cls, key: str) -> bool:
        """Verifica si un lock está activo."""
        return cache.get(key) is not None
    
    @classmethod
    def get_lock_info(cls, key: str) -> dict:
        """Obtiene información sobre un lock (para debugging)."""
        token = cache.get(key)
        ttl = cache.ttl(key)
        return {
            'locked': token is not None,
            'token': token[:8] + '...' if token else None,
            'ttl_seconds': ttl
        }


def with_lock(key: str, timeout: int = 15, retries: int = 3, backoff: float = 0.5):
    """
    Decorador para adquirir locks distribuidos con retry y exponential backoff.
    
    Args:
        key: Clave del lock en Redis
        timeout: Tiempo de expiración del lock en segundos
        retries: Número máximo de reintentos
        backoff: Tiempo base para exponential backoff (segundos)
    
    Ejemplo:
        @with_lock('stock:producto:{id}', timeout=10, retries=3)
        def descontar_stock(producto_id, cantidad):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Resolver la clave del lock (puede contener placeholders)
            lock_key = key.format(*args, **kwargs) if args else key
            token = str(uuid.uuid4())
            
            attempt = 0
            while attempt <= retries:
                try:
                    # Intentar adquirir el lock
                    if LockManager.acquire(lock_key, timeout=timeout, token=token):
                        try:
                            # Ejecutar la función protegida
                            return func(*args, **kwargs)
                        finally:
                            # Liberar el lock (siempre, incluso si hay error)
                            try:
                                LockManager.release(lock_key, token)
                            except Exception as release_error:
                                logger.error(f"Error liberando lock {lock_key}: {release_error}")
                    else:
                        # Lock no disponible, esperar con exponential backoff (limitado)
                        wait_time = min(backoff * (2 ** attempt), cls.MAX_BACKOFF)
                        logger.warning(
                            f"Lock ocupado {lock_key}, intento {attempt + 1}/{retries}. "
                            f"Esperando {wait_time}s"
                        )
                        time.sleep(wait_time)
                        attempt += 1
                        
                except Exception as e:
                    logger.error(f"Error en lock {lock_key}: {str(e)}")
                    # Intentar liberar lock en caso de error (puede que no se haya adquirido)
                    try:
                        LockManager.release(lock_key, token)
                    except Exception:
                        pass  # El lock puede no haberse adquirido aún
                    raise
            
            # Se agotaron los reintentos
            error_msg = f"Timeout adquiriendo lock: {lock_key} después de {retries} intentos"
            logger.error(error_msg)
            from apps.core.errors import ErrorResponse
            raise ErrorResponse(
                code='LOCK_TIMEOUT',
                message=error_msg,
                status_code=408
            )
        
        return wrapper
    return decorator


class DistributedLock:
    """
    Context manager para locks distribuidos.
    Uso: with DistributedLock('key'): ...
    """
    
    def __init__(self, key: str, timeout: int = 15, retries: int = 3, backoff: float = 0.5):
        self.key = key
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.token = None
    
    def __enter__(self):
        attempt = 0
        while attempt <= self.retries:
            self.token = str(uuid.uuid4())
            if LockManager.acquire(self.key, timeout=self.timeout, token=self.token):
                return self
            
            wait_time = self.backoff * (2 ** attempt)
            logger.warning(f"Lock ocupado {self.key}, esperando {wait_time}s")
            time.sleep(wait_time)
            attempt += 1
        
        raise TimeoutError(f"No se pudo adquirir el lock: {self.key}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            try:
                LockManager.release(self.key, self.token)
            except Exception as e:
                logger.error(f"Error liberando lock en __exit__: {e}")
        return False
