"""
Services para la app de Inventario.
Lógica de negocio pura, separada de las views.
"""
from django.db import transaction
from django.core.cache import cache
from apps.inventory.models import Producto, Entrada
from apps.core.locks import with_lock
from apps.core.audit import AuditLogger
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

CACHE_KEY_PRODUCTOS = "productos_lista"
CACHE_TIMEOUT = 60  # segundos


def get_productos_cached():
    """Obtiene lista de productos desde caché Redis."""
    data = cache.get(CACHE_KEY_PRODUCTOS)
    if data is None:
        productos = list(Producto.objects.all().values())
        # Convertir Decimal a str para serialización JSON
        for p in productos:
            p['precio'] = str(p['precio'])
        cache.set(CACHE_KEY_PRODUCTOS, productos, CACHE_TIMEOUT)
        return productos
    return data


def invalidate_producto_cache():
    """Invalida la caché de productos."""
    cache.delete(CACHE_KEY_PRODUCTOS)


@with_lock(key="lock_producto_create", timeout=15, retries=3, backoff=0.5)
@transaction.atomic
def crear_producto(datos, usuario=None):
    """
    Crea un nuevo producto con lock distribuido.
    """
    try:
        producto = Producto.objects.create(
            nombre=datos['nombre'],
            stock=datos.get('stock', 0),
            precio=Decimal(str(datos['precio']))
        )
        
        AuditLogger.log(
            action="PRODUCTO_CREADO",
            details={"producto_id": producto.id, "nombre": producto.nombre},
            estado="SUCCESS",
            usuario=usuario
        )
        
        invalidate_producto_cache()
        
        return {
            "id": producto.id,
            "nombre": producto.nombre,
            "stock": producto.stock,
            "precio": str(producto.precio)
        }
    except Exception as e:
        AuditLogger.log(
            action="PRODUCTO_CREACION_FALLIDA",
            details={"error": str(e)},
            estado="ERROR",
            usuario=usuario
        )
        raise e


@with_lock(key="lock_producto_update:{producto_id}", timeout=15, retries=3, backoff=0.5)
@transaction.atomic
def actualizar_producto(producto_id, datos, usuario=None):
    """
    Actualiza un producto existente e invalida caché.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
        producto.nombre = datos.get('nombre', producto.nombre)
        producto.stock = datos.get('stock', producto.stock)
        producto.precio = Decimal(str(datos.get('precio', producto.precio)))
        producto.save()
        
        AuditLogger.log(
            action="PRODUCTO_ACTUALIZADO",
            details={"producto_id": producto.id},
            estado="SUCCESS",
            usuario=usuario
        )
        
        invalidate_producto_cache()
        
        return {
            "id": producto.id,
            "nombre": producto.nombre,
            "stock": producto.stock,
            "precio": str(producto.precio)
        }
    except Producto.DoesNotExist:
        raise ValueError(f"Producto {producto_id} no encontrado")
    except Exception as e:
        AuditLogger.log(
            action="PRODUCTO_ACTUALIZACION_FALLIDA",
            details={"producto_id": producto_id, "error": str(e)},
            estado="ERROR",
            usuario=usuario
        )
        raise e


@with_lock(key="lock_producto_delete:{producto_id}", timeout=15, retries=3, backoff=0.5)
@transaction.atomic
def eliminar_producto(producto_id, usuario=None):
    """
    Elimina un producto e invalida caché.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
        nombre = producto.nombre
        producto.delete()
        
        AuditLogger.log(
            action="PRODUCTO_ELIMINADO",
            details={"producto_id": producto_id, "nombre": nombre},
            estado="SUCCESS",
            usuario=usuario
        )
        
        invalidate_producto_cache()
        
        return {"mensaje": f"Producto {nombre} eliminado"}
    except Producto.DoesNotExist:
        raise ValueError(f"Producto {producto_id} no encontrado")
    except Exception as e:
        AuditLogger.log(
            action="PRODUCTO_ELIMINACION_FALLIDA",
            details={"producto_id": producto_id, "error": str(e)},
            estado="ERROR",
            usuario=usuario
        )
        raise e


def registrar_entrada(producto_id, cantidad, costo, usuario=None):
    """Registra una entrada de inventario."""
    try:
        producto = Producto.objects.get(id=producto_id)
        entrada = Entrada.objects.create(
            producto=producto,
            cantidad=cantidad,
            costo=Decimal(str(costo))
        )
        
        # Actualizar stock
        producto.stock += cantidad
        producto.save()
        
        AuditLogger.log(
            action="ENTRADA_REGISTRADA",
            details={"entrada_id": entrada.id, "cantidad": cantidad},
            estado="SUCCESS",
            usuario=usuario
        )
        
        invalidate_producto_cache()
        
        return {"id": entrada.id, "nuevo_stock": producto.stock}
    except Producto.DoesNotExist:
        raise ValueError(f"Producto {producto_id} no encontrado")
    except Exception as e:
        AuditLogger.log(
            action="ENTRADA_FALLIDA",
            details={"error": str(e)},
            estado="ERROR",
            usuario=usuario
        )
        raise e
