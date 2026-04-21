"""
ProductCache - Sistema de caché para productos usando Redis.
TTL: 60 segundos. Invalidación automática en mutaciones.
"""
import logging
from typing import Optional, List, Dict, Any
from django.core.cache import cache
from django.db.models import Model

logger = logging.getLogger(__name__)


class ProductCache:
    """
    Gestiona el caché de productos con Redis.
    TTL: 60 segundos por defecto.
    """
    
    TTL = 60  # segundos
    PREFIX = f"microerp:{os.environ.get('DJANGO_SETTINGS_MODULE', 'development')}:product"
    ALL_PRODUCTS_KEY = f'{PREFIX}:all'
    
    @classmethod
    def get_product(cls, product_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un producto del caché por su ID."""
        key = f'{cls.PREFIX}:{product_id}'
        data = cache.get(key)
        
        if data:
            logger.debug(f"Caché HIT: {key}")
            return data
        
        logger.debug(f"Caché MISS: {key}")
        return None
    
    @classmethod
    def set_product(cls, product_id: str, data: Dict[str, Any], ttl: int = None) -> bool:
        """
        Guarda un producto en el caché.
        
        Args:
            product_id: ID del producto
            data: Diccionario con los datos del producto
            ttl: Tiempo de vida en segundos (default: 60)
        """
        key = f'{cls.PREFIX}:{product_id}'
        ttl = ttl or cls.TTL
        
        try:
            cache.set(key, data, timeout=ttl)
            logger.debug(f"Producto cacheado: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error cacheando producto {product_id}: {str(e)}")
            return False
    
    @classmethod
    def invalidate(cls, product_id: str) -> bool:
        """Invalida el caché de un producto específico."""
        key = f'{cls.PREFIX}:{product_id}'
        
        try:
            cache.delete(key)
            logger.debug(f"Caché invalidado: {key}")
            return True
        except Exception as e:
            logger.error(f"Error invalidando caché {product_id}: {str(e)}")
            return False
    
    @classmethod
    def invalidate_all(cls) -> bool:
        """Invalida todo el caché de productos."""
        try:
            # Usar patrón de clave para borrar todos los productos
            pattern = f'{cls.PREFIX}:*'
            
            # Obtener todas las claves que coinciden
            from django.core.cache import caches
            redis_client = caches['default'].client.get_client()
            
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Caché de productos completamente invalidado ({len(keys)} claves)")
            
            return True
        except Exception as e:
            logger.error(f"Error invalidando todo el caché: {str(e)}")
            return False
    
    @classmethod
    def get_all_products(cls) -> Optional[List[Dict[str, Any]]]:
        """Obtiene la lista de todos los productos desde el caché."""
        data = cache.get(cls.ALL_PRODUCTS_KEY)
        
        if data:
            logger.debug(f"Caché HIT: {cls.ALL_PRODUCTS_KEY}")
            return data
        
        logger.debug(f"Caché MISS: {cls.ALL_PRODUCTS_KEY}")
        return None
    
    @classmethod
    def set_all_products(cls, products: List[Dict[str, Any]], ttl: int = None) -> bool:
        """Guarda la lista de todos los productos en el caché."""
        ttl = ttl or cls.TTL
        
        try:
            cache.set(cls.ALL_PRODUCTS_KEY, products, timeout=ttl)
            logger.debug(f"Lista de productos cacheada (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error cacheando lista de productos: {str(e)}")
            return False
    
    @classmethod
    def cache_or_get(cls, product_id: str, fetch_func) -> Optional[Dict[str, Any]]:
        """
        Obtiene del caché o ejecuta fetch_func y cachea el resultado.
        
        Args:
            product_id: ID del producto
            fetch_func: Función que obtiene los datos si no están en caché
        
        Returns:
            Datos del producto o None
        """
        # Intentar obtener del caché
        data = cls.get_product(product_id)
        
        if data is not None:
            return data
        
        # Ejecutar fetch_func y cachea
        try:
            data = fetch_func()
            if data:
                cls.set_product(product_id, data)
            return data
        except Exception as e:
            logger.error(f"Error obteniendo producto {product_id}: {str(e)}")
            return None


def cache_product(func):
    """
    Decorador para cachear automáticamente el resultado de una función.
    Asume que el primer argumento es product_id.
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        product_id = args[0] if args else kwargs.get('product_id')
        
        if not product_id:
            return func(*args, **kwargs)
        
        # Intentar obtener del caché
        cached_data = ProductCache.get_product(product_id)
        if cached_data:
            return cached_data
        
        # Ejecutar función y cachea
        result = func(*args, **kwargs)
        
        if result:
            ProductCache.set_product(product_id, result)
        
        return result
    
    return wrapper
