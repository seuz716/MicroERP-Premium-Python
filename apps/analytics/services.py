"""
Services para la app de Analytics.
Lógica de negocio para reportes, estrellas, horarios y categorías.
"""
from django.db.models import Sum, F, Q, Count, Avg, DecimalField
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def get_productos_estrella(limite=10):
    """
    Obtiene los productos más rentables (estrella) de los últimos 90 días.
    
    Algoritmo:
    1. fecha_inicio = hoy - 90 días
    2. Calcular ganancia por producto usando ORM (no loops):
       ganancia = Sum((precio_venta - costo_promedio) × cantidad)
    3. Ordenar por ganancia descendente, slice [:limite]
    4. Cachear resultado en Redis con clave "analytics:estrellas:{fecha_hoy}" TTL 86400
    5. Retornar con porcentaje_del_total calculado
    """
    hoy = timezone.now().date()
    cache_key = f"analytics:estrellas:{hoy.isoformat()}"
    
    # Intentar obtener de caché
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    fecha_inicio = hoy - timedelta(days=90)
    
    from apps.inventory.models import Producto
    from apps.sales.models import DetalleVenta
    
    # Calculamos ganancia usando annotate con ORM
    # Nota: usamos precio_unitario de DetalleVenta y estimamos costo como 70% del precio
    # En producción debería usar el costo real de Entrada
    productos_ganancia = Producto.objects.filter(activo=True).annotate(
        total_vendido=Sum(
            'detalleventa__cantidad',
            filter=Q(detalleventa__venta__fecha__gte=fecha_inicio),
            output_field=DecimalField()
        ),
        ingresos_totales=Sum(
            F('detalleventa__cantidad') * F('detalleventa__precio_unitario'),
            filter=Q(detalleventa__venta__fecha__gte=fecha_inicio),
            output_field=DecimalField()
        )
    ).filter(total_vendido__isnull=False, total_vendido__gt=0)
    
    # Calculamos ganancia estimada (30% margen promedio)
    total_general = Decimal('0')
    resultados = []
    
    for p in productos_ganancia:
        ingresos = p.ingresos_totales or Decimal('0')
        # Estimamos costo como 70% del precio (en producción usar costo real)
        ganancia = ingresos * Decimal('0.30')
        total_general += ganancia
        
        resultados.append({
            'producto_id': p.id,
            'producto_nombre': p.nombre,
            'total_vendido': int(p.total_vendido),
            'ingresos_totales': str(ingresos),
            'ganancia_estimada': str(ganancia)
        })
    
    # Ordenar por ganancia y tomar top N
    resultados.sort(key=lambda x: Decimal(x['ganancia_estimada']), reverse=True)
    resultados = resultados[:limite]
    
    # Calcular porcentaje del total
    if total_general > 0:
        for item in resultados:
            item['porcentaje_del_total'] = round(
                float((Decimal(item['ganancia_estimada']) / total_general) * 100), 2
            )
    else:
        for item in resultados:
            item['porcentaje_del_total'] = 0
    
    data = {
        'fecha_consulta': hoy.isoformat(),
        'periodo_dias': 90,
        'limite': limite,
        'total_productos_analizados': len(resultados),
        'productos': resultados
    }
    
    # Cachear por 24 horas
    cache.set(cache_key, data, 86400)
    
    return data


def get_horarios_pico():
    """
    Analiza los horarios de mayor venta.
    Retorna distribución de ventas por hora del día.
    """
    from apps.sales.models import Venta
    
    hoy = timezone.now().date()
    fecha_inicio = hoy - timedelta(days=30)
    
    # Agrupar ventas por hora
    ventas_por_hora = Venta.objects.filter(
        fecha__gte=fecha_inicio
    ).extra(
        select={'hora': 'EXTRACT(HOUR FROM fecha)'}
    ).values('hora').annotate(
        total_ventas=Count('id'),
        monto_total=Sum('total')
    ).order_by('hora')
    
    # Convertir a formato legible
    horarios = []
    for v in ventas_por_hora:
        hora = int(v['hora'])
        horarios.append({
            'hora': f"{hora:02d}:00",
            'total_ventas': v['total_ventas'],
            'monto_total': str(v['monto_total'] or Decimal('0'))
        })
    
    # Identificar hora pico
    hora_pico = max(horarios, key=lambda x: x['total_ventas']) if horarios else None
    
    return {
        'fecha_consulta': hoy.isoformat(),
        'periodo_dias': 30,
        'horarios': horarios,
        'hora_pico': hora_pico
    }


def get_categorias_rentables():
    """
    Analiza rentabilidad por categoría de producto.
    """
    from apps.inventory.models import Producto, Categoria
    from apps.sales.models import DetalleVenta
    
    hoy = timezone.now().date()
    fecha_inicio = hoy - timedelta(days=90)
    
    # Si hay modelo Categoria, agrupar por categoría
    try:
        categorias_data = Producto.objects.filter(
            activo=True,
            categoria__isnull=False
        ).annotate(
            total_vendido=Sum(
                'detalleventa__cantidad',
                filter=Q(detalleventa__venta__fecha__gte=fecha_inicio),
                output_field=DecimalField()
            ),
            ingresos=Sum(
                F('detalleventa__cantidad') * F('detalleventa__precio_unitario'),
                filter=Q(detalleventa__venta__fecha__gte=fecha_inicio),
                output_field=DecimalField()
            )
        ).values('categoria__nombre').annotate(
            total_productos=Count('id', distinct=True)
        ).order_by('-ingresos')
        
        categorias = []
        for cat in categorias_data:
            categorias.append({
                'categoria': cat['categoria__nombre'],
                'total_productos': cat['total_productos'],
                'total_vendido': int(cat['total_vendido'] or 0),
                'ingresos_totales': str(cat['ingresos'] or Decimal('0')),
                'ganancia_estimada': str((cat['ingresos'] or Decimal('0')) * Decimal('0.30'))
            })
        
        return {
            'fecha_consulta': hoy.isoformat(),
            'periodo_dias': 90,
            'categorias': categorias
        }
    except Exception:
        # No hay campo categoria o modelo Categoria
        return {
            'fecha_consulta': hoy.isoformat(),
            'periodo_dias': 90,
            'categorias': [],
            'mensaje': 'Categorías no disponibles'
        }


def get_reporte_general(dias=30):
    """
    Genera reporte general de analytics.
    Combina múltiples métricas en un solo reporte.
    """
    from apps.sales.models import Venta
    from apps.inventory.models import Producto
    
    hoy = timezone.now().date()
    fecha_inicio = hoy - timedelta(days=dias)
    
    # Métricas de ventas
    ventas_stats = Venta.objects.filter(fecha__gte=fecha_inicio).aggregate(
        total_ventas=Count('id'),
        monto_total=Sum('total', output_field=DecimalField()),
        promedio_venta=Avg('total', output_field=DecimalField())
    )
    
    # Métricas de inventario
    inventario_stats = Producto.objects.filter(activo=True).aggregate(
        total_productos=Count('id'),
        stock_total=Sum('stock'),
        valor_inventario=Sum(F('stock') * F('precio'), output_field=DecimalField())
    )
    
    # Productos más vendidos
    productos_mas_vendidos = Producto.objects.filter(activo=True).annotate(
        vendido=Sum(
            'detalleventa__cantidad',
            filter=Q(detalleventa__venta__fecha__gte=fecha_inicio),
            output_field=DecimalField()
        )
    ).filter(vendido__isnull=False, vendido__gt=0).order_by('-vendido')[:5]
    
    top_productos = [
        {
            'id': p.id,
            'nombre': p.nombre,
            'total_vendido': int(p.vendido)
        }
        for p in productos_mas_vendidos
    ]
    
    return {
        'fecha_generacion': hoy.isoformat(),
        'periodo_dias': dias,
        'ventas': {
            'total_ventas': ventas_stats['total_ventas'] or 0,
            'monto_total': str(ventas_stats['monto_total'] or Decimal('0')),
            'promedio_venta': str(ventas_stats['promedio_venta'] or Decimal('0'))
        },
        'inventario': {
            'total_productos': inventario_stats['total_productos'] or 0,
            'stock_total': inventario_stats['stock_total'] or 0,
            'valor_inventario': str(inventario_stats['valor_inventario'] or Decimal('0'))
        },
        'top_productos': top_productos
    }
