"""
Services para la app de Ventas.
Lógica de negocio ATÓMICA para procesar ventas.
"""
from django.db import transaction
from django.core.cache import cache
from django.db.models import Sum, F, DecimalField, Count
from datetime import datetime, timedelta
from decimal import Decimal
from apps.sales.models import Venta, DetalleVenta
from apps.inventory.models import Producto
from apps.core.locks import with_lock
from apps.core.audit import AuditLogger
import logging

logger = logging.getLogger(__name__)


@transaction.atomic
def procesar_venta(cart_items, usuario=None):
    """
    Procesa una venta de forma ATÓMICA:
    1. Valida carrito no vacío
    2. Para cada item: verifica stock con lock
    3. Desconta stock
    4. Crea Venta + Detalles
    5. Si falla: rollback total
    6. Invalida caché de productos
    """
    if not cart_items:
        raise ValueError("El carrito está vacío")

    venta = Venta.objects.create(total=Decimal('0'))
    total_venta = Decimal('0')
    productos_afectados = []

    try:
        for item in cart_items:
            producto_id = item.get('producto_id') or item.get('id')
            cantidad = int(item['cantidad'])
            
            # Lock distribuido por producto para evitar race conditions
            lock_key = f"lock_stock:{producto_id}"
            
            # Obtenemos el producto con select_for_update dentro del lock
            try:
                producto = Producto.objects.select_for_update().get(id=producto_id)
            except Producto.DoesNotExist:
                raise ValueError(f"Producto {producto_id} no encontrado")

            if producto.stock < cantidad:
                raise ValueError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")

            # Descontar stock
            producto.stock -= cantidad
            producto.save()
            productos_afectados.append(producto_id)

            # Crear detalle de venta
            subtotal = producto.precio * cantidad
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )
            total_venta += subtotal

        # Actualizar total de la venta
        venta.total = total_venta
        venta.save()

        # Invalidar caché de productos
        cache.delete("productos_lista")

        AuditLogger.log(
            action="VENTA_PROCESADA",
            details={
                "venta_id": venta.id,
                "total": str(total_venta),
                "items": len(cart_items)
            },
            estado="SUCCESS",
            usuario=usuario
        )

        return {
            "id_venta": venta.id,
            "total": str(total_venta),
            "fecha": venta.fecha.isoformat(),
            "items": len(cart_items)
        }

    except Exception as e:
        AuditLogger.log(
            action="VENTA_FALLIDA",
            details={"error": str(e)},
            estado="ERROR",
            usuario=usuario
        )
        # transaction.atomic() hace rollback automático
        raise e


def get_historial_ventas(limite=50):
    """Obtiene las últimas N ventas."""
    ventas = Venta.objects.select_related().order_by('-fecha')[:limite]
    return [
        {
            "id": v.id,
            "fecha": v.fecha.isoformat(),
            "total": str(v.total),
            "detalle_count": v.detalles.count()
        }
        for v in ventas
    ]


def get_dashboard_kpis():
    """
    Obtiene KPIs del día:
    - Ventas hoy
    - Utilidad del día
    - Stock total
    - Valor de inventario
    
    OPTIMIZADO: Usa aggregate() en lugar de loops Python
    """
    hoy = datetime.now().date()
    
    # Ventas de hoy con aggregate (1 query)
    ventas_stats = Venta.objects.filter(fecha__date=hoy).aggregate(
        total_count=Count('id'),
        monto_total=Sum('total', output_field=DecimalField())
    )
    total_ventas_hoy = ventas_stats['total_count'] or 0
    monto_ventas_hoy = ventas_stats['monto_total'] or Decimal('0')
    
    # Calculamos utilidad (precio - costo promedio estimado)
    # En producción esto debería usar el costo real del producto
    utilidad_hoy = monto_ventas_hoy * Decimal('0.3')  # Estimado 30% margen
    
    # Stock total e inventario con aggregate (1 query)
    inventario_stats = Producto.objects.aggregate(
        total_stock=Sum('stock'),
        valor_inventario=Sum(F('stock') * F('precio'), output_field=DecimalField())
    )
    stock_total = inventario_stats['total_stock'] or 0
    valor_inventario = inventario_stats['valor_inventario'] or Decimal('0')
    
    return {
        "ventas_hoy": total_ventas_hoy,
        "monto_ventas_hoy": str(monto_ventas_hoy),
        "utilidad_hoy": str(utilidad_hoy),
        "stock_total": stock_total,
        "valor_inventario": str(valor_inventario),
        "fecha": hoy.isoformat()
    }
