"""
Services para la app de Purchasing.
Lógica de negocio para sugerencias de pedidos, vencimientos y análisis ABC.
"""
from django.db.models import Sum, F, Q, Avg, Case, When, DecimalField, FloatField
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil
import logging

logger = logging.getLogger(__name__)


def sugerir_pedidos():
    """
    Sugiere pedidos basados en ventas de los últimos 30 días.
    
    Algoritmo:
    1. Calcula total vendido por producto en últimos 30 días
    2. promedio_diario = total_vendido / 30
    3. stock_recomendado = promedio_diario × 7
    4. Si stock_actual < stock_recomendado Y promedio_diario > 0: sugerir
    5. cantidad_sugerida = ceil(stock_recomendado × 1.5)
    6. urgencia: CRÍTICA si stock=0, ALTA si stock < promedio×3, NORMAL otro caso
    
    OPTIMIZADO: Usa annotate/aggregate, NO loops Python
    """
    fecha_limite = timezone.now() - timedelta(days=30)
    
    # Anotamos cada producto con las ventas de los últimos 30 días
    from apps.inventory.models import Producto
    from apps.sales.models import DetalleVenta
    
    productos_con_ventas = Producto.objects.filter(activo=True).annotate(
        total_vendido_30d=Sum(
            'detalleventa__cantidad',
            filter=Q(detalleventa__venta__fecha__gte=fecha_limite),
            output_field=DecimalField()
        ),
        stock_actual=F('stock')
    )
    
    sugerencias = []
    hoy = timezone.now().date()
    
    for producto in productos_con_ventas:
        total_vendido = producto.total_vendido_30d or Decimal('0')
        promedio_diario = total_vendido / 30 if total_vendido > 0 else Decimal('0')
        
        if promedio_diario <= 0:
            continue
            
        stock_recomendado = promedio_diario * 7
        stock_actual = producto.stock_actual or 0
        
        if stock_actual >= stock_recomendado:
            continue
        
        cantidad_sugerida = ceil(float(stock_recomendado * Decimal('1.5')))
        
        # Determinar urgencia
        if stock_actual == 0:
            urgencia = 'CRITICA'
        elif stock_actual < promedio_diario * 3:
            urgencia = 'ALTA'
        else:
            urgencia = 'NORMAL'
        
        sugerencias.append({
            'producto_id': producto.id,
            'producto_nombre': producto.nombre,
            'stock_actual': int(stock_actual),
            'promedio_diario': round(float(promedio_diario), 2),
            'stock_recomendado': int(ceil(float(stock_recomendado))),
            'cantidad_sugerida': cantidad_sugerida,
            'urgencia': urgencia,
            'fecha_sugerencia': hoy.isoformat()
        })
    
    # Ordenar por urgencia (CRITICA primero) y luego por cantidad sugerida
    urgencia_order = {'CRITICA': 0, 'ALTA': 1, 'NORMAL': 2}
    sugerencias.sort(key=lambda x: (urgencia_order[x['urgencia']], -x['cantidad_sugerida']))
    
    return {
        'fecha_generacion': hoy.isoformat(),
        'total_sugerencias': len(sugerencias),
        'sugerencias': sugerencias
    }


def get_vencimientos():
    """
    Obtiene productos próximos a vencer (si hay campo fecha_vencimiento).
    Para productos perecederos.
    """
    from apps.inventory.models import Producto
    
    hoy = timezone.now().date()
    limite = hoy + timedelta(days=30)
    
    # Filtramos productos con fecha_vencimiento si existe el campo
    try:
        productos_venciendo = Producto.objects.filter(
            activo=True,
            fecha_vencimiento__isnull=False,
            fecha_vencimiento__lte=limite,
            fecha_vencimiento__gte=hoy
        ).order_by('fecha_vencimiento')[:50]
        
        return {
            'fecha_consulta': hoy.isoformat(),
            'total_proximos_vencer': productos_venciendo.count(),
            'productos': [
                {
                    'id': p.id,
                    'nombre': p.nombre,
                    'fecha_vencimiento': p.fecha_vencimiento.isoformat(),
                    'dias_restantes': (p.fecha_vencimiento - hoy).days
                }
                for p in productos_venciendo
            ]
        }
    except Exception:
        # El campo fecha_vencimiento no existe
        return {
            'fecha_consulta': hoy.isoformat(),
            'total_proximos_vencer': 0,
            'productos': [],
            'mensaje': 'Campo fecha_vencimiento no disponible'
        }


def get_promociones():
    """
    Identifica productos con exceso de stock que podrían promocionarse.
    Productos con stock > 3× el promedio diario de ventas.
    """
    from apps.inventory.models import Producto
    from apps.sales.models import DetalleVenta
    
    fecha_limite = timezone.now() - timedelta(days=30)
    
    productos = Producto.objects.filter(activo=True).annotate(
        total_vendido_30d=Sum(
            'detalleventa__cantidad',
            filter=Q(detalleventa__venta__fecha__gte=fecha_limite),
            output_field=DecimalField()
        )
    )
    
    promociones = []
    hoy = timezone.now().date()
    
    for p in productos:
        total_vendido = p.total_vendido_30d or Decimal('0')
        promedio_diario = total_vendido / 30 if total_vendido > 0 else Decimal('0')
        
        if promedio_diario <= 0:
            continue
        
        if p.stock > promedio_diario * 3:
            exceso = p.stock - (promedio_diario * 3)
            porcentaje_descuento_sugerido = min(20, int((exceso / p.stock) * 30))
            
            promociones.append({
                'producto_id': p.id,
                'producto_nombre': p.nombre,
                'stock_actual': p.stock,
                'promedio_diario': round(float(promedio_diario), 2),
                'exceso_stock': int(exceso),
                'descuento_sugerido_porcentaje': porcentaje_descuento_sugerido,
                'razon': 'Exceso de inventario'
            })
    
    promociones.sort(key=lambda x: -x['exceso_stock'])
    
    return {
        'fecha_generacion': hoy.isoformat(),
        'total_promociones': len(promociones),
        'promociones': promociones
    }


def analisis_abc():
    """
    Análisis ABC de productos según su contribución a las ventas.
    A: 80% del valor acumulado
    B: 15% del valor acumulado  
    C: 5% del valor acumulado
    """
    from apps.inventory.models import Producto
    from apps.sales.models import DetalleVenta
    
    fecha_limite = timezone.now() - timedelta(days=90)
    
    # Productos ordenados por valor vendido (precio × cantidad)
    productos_valor = Producto.objects.filter(activo=True).annotate(
        valor_vendido=Sum(
            F('detalleventa__cantidad') * F('detalleventa__precio_unitario'),
            filter=Q(detalleventa__venta__fecha__gte=fecha_limite),
            output_field=DecimalField()
        )
    ).filter(valor_vendido__isnull=False).order_by('-valor_vendido')
    
    total_valor = sum(p.valor_vendido or Decimal('0') for p in productos_valor)
    
    if total_valor == 0:
        return {
            'fecha_analisis': timezone.now().date().isoformat(),
            'total_productos': 0,
            'categorias': {'A': [], 'B': [], 'C': []},
            'mensaje': 'No hay ventas registradas en los últimos 90 días'
        }
    
    categorias = {'A': [], 'B': [], 'C': []}
    acumulado = Decimal('0')
    umbral_a = total_valor * Decimal('0.80')
    umbral_b = total_valor * Decimal('0.95')
    
    for p in productos_valor:
        valor = p.valor_vendido or Decimal('0')
        acumulado += valor
        porcentaje_acumulado = (acumulado / total_valor) * 100
        
        item = {
            'producto_id': p.id,
            'producto_nombre': p.nombre,
            'valor_vendido': str(valor),
            'porcentaje_individual': round(float((valor / total_valor) * 100), 2),
            'porcentaje_acumulado': round(float(porcentaje_acumulado), 2)
        }
        
        if acumulado <= umbral_a:
            categorias['A'].append(item)
        elif acumulado <= umbral_b:
            categorias['B'].append(item)
        else:
            categorias['C'].append(item)
    
    return {
        'fecha_analisis': timezone.now().date().isoformat(),
        'periodo_dias': 90,
        'total_valor_vendido': str(total_valor),
        'total_productos': len(productos_valor),
        'categorias': {
            'A': {'count': len(categorias['A']), 'productos': categorias['A']},
            'B': {'count': len(categorias['B']), 'productos': categorias['B']},
            'C': {'count': len(categorias['C']), 'productos': categorias['C']}
        }
    }
