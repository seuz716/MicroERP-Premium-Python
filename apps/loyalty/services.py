"""
Services para la app de Loyalty.
Lógica de negocio para puntos, niveles y tickets.
"""
from django.db import transaction
from django.db.models import Sum, F
from decimal import Decimal
from datetime import datetime
from apps.core.audit import AuditLogger
import logging

logger = logging.getLogger(__name__)

# Niveles y sus beneficios
NIVELES = {
    'BRONZE': {'min': 0, 'max': 499, 'descuento': 0},
    'SILVER': {'min': 500, 'max': 1999, 'descuento': 1},
    'GOLD': {'min': 2000, 'max': 4999, 'descuento': 2},
    'PLATINUM': {'min': 5000, 'max': float('inf'), 'descuento': 5}
}


def calcular_nivel(puntos):
    """Determina el nivel según los puntos acumulados."""
    for nivel, datos in NIVELES.items():
        if datos['min'] <= puntos <= datos['max']:
            return nivel
    return 'PLATINUM'


@transaction.atomic
def acumular_puntos(id_cliente, monto_venta, usuario=None):
    """
    Acumula puntos por una venta: 1 punto por $1.
    
    Flujo:
    1. Calcular puntos = floor(monto_venta × 1.0)
    2. Sumar a puntos actuales del cliente (con select_for_update)
    3. Recalcular nivel
    4. Si cambia de nivel: incluir bonus
    5. Retornar información actualizada
    """
    from apps.loyalty.models import ClienteLoyalty
    
    # Usamos select_for_update para evitar race conditions
    cliente = ClienteLoyalty.objects.select_for_update().get(id=id_cliente)
    
    puntos_actuales = cliente.puntos or 0
    nivel_anterior = cliente.nivel or 'BRONZE'
    
    # Calcular nuevos puntos (1 punto por $1)
    puntos_ganados = int(monto_venta)  # floor implícito al convertir a int
    nuevos_puntos = puntos_actuales + puntos_ganados
    
    # Actualizar cliente
    cliente.puntos = nuevos_puntos
    nuevo_nivel = calcular_nivel(nuevos_puntos)
    cliente.nivel = nuevo_nivel
    cliente.save()
    
    # Verificar si subió de nivel
    subio_nivel = False
    bonus_descuento = 0
    
    if nuevo_nivel != nivel_anterior:
        subio_nivel = True
        bonus_descuento = NIVELES[nuevo_nivel]['descuento']
        
        AuditLogger.log(
            action="CLIENTE_SUBIO_NIVEL",
            details={
                "cliente_id": id_cliente,
                "nivel_anterior": nivel_anterior,
                "nuevo_nivel": nuevo_nivel,
                "bonus_descuento": bonus_descuento
            },
            estado="SUCCESS",
            usuario=usuario
        )
    
    AuditLogger.log(
        action="PUNTOS_ACUMULADOS",
        details={
            "cliente_id": id_cliente,
            "monto_venta": str(monto_venta),
            "puntos_ganados": puntos_ganados,
            "puntos_totales": nuevos_puntos
        },
        estado="SUCCESS",
        usuario=usuario
    )
    
    resultado = {
        "id_cliente": id_cliente,
        "puntos_anteriores": puntos_actuales,
        "puntos_ganados": puntos_ganados,
        "puntos_totales": nuevos_puntos,
        "nivel_actual": nuevo_nivel,
        "descuento_aplicable_porcentaje": NIVELES[nuevo_nivel]['descuento']
    }
    
    if subio_nivel:
        resultado["subio_nivel"] = True
        resultado["nivel_anterior"] = nivel_anterior
        resultado["bonus_descuento"] = bonus_descuento
    
    return resultado


@transaction.atomic
def canjear_puntos(id_cliente, puntos_a_canjear, usuario=None):
    """
    Canjea puntos por descuento o premio.
    
    Valida DENTRO de la transacción que los puntos sean suficientes.
    """
    from apps.loyalty.models import ClienteLoyalty
    
    # select_for_update para evitar canje doble
    cliente = ClienteLoyalty.objects.select_for_update().get(id=id_cliente)
    
    puntos_actuales = cliente.puntos or 0
    
    # Validación DENTRO de la transacción
    if puntos_a_canjear > puntos_actuales:
        raise ValueError(f"Puntos insuficientes. Disponibles: {puntos_actuales}, Solicitados: {puntos_a_canjear}")
    
    # Descontar puntos
    cliente.puntos = puntos_actuales - puntos_a_canjear
    
    # Recalcular nivel después del canje
    nuevo_nivel = calcular_nivel(cliente.puntos)
    cliente.nivel = nuevo_nivel
    cliente.save()
    
    AuditLogger.log(
        action="PUNTOS_CANJEAOS",
        details={
            "cliente_id": id_cliente,
            "puntos_canjeados": puntos_a_canjear,
            "puntos_restantes": cliente.puntos
        },
        estado="SUCCESS",
        usuario=usuario
    )
    
    return {
        "id_cliente": id_cliente,
        "puntos_canjeados": puntos_a_canjear,
        "puntos_restantes": cliente.puntos,
        "nivel_actual": nuevo_nivel,
        "descuento_aplicable_porcentaje": NIVELES[nuevo_nivel]['descuento']
    }


@transaction.atomic
def crear_ticket(cliente_id, asunto, descripcion, usuario=None):
    """Crea un ticket de soporte para un cliente."""
    from apps.loyalty.models import TicketSoporte
    
    ticket = TicketSoporte.objects.create(
        cliente_id=cliente_id,
        asunto=asunto,
        descripcion=descripcion,
        estado='ABIERTO'
    )
    
    AuditLogger.log(
        action="TICKET_CREADO",
        details={"ticket_id": ticket.id, "cliente_id": cliente_id},
        estado="SUCCESS",
        usuario=usuario
    )
    
    return {
        "id_ticket": ticket.id,
        "estado": ticket.estado,
        "fecha_creacion": ticket.fecha_creacion.isoformat()
    }


def get_cliente_info(id_cliente):
    """Obtiene información completa de un cliente loyalty."""
    from apps.loyalty.models import ClienteLoyalty
    
    try:
        cliente = ClienteLoyalty.objects.get(id=id_cliente)
        return {
            "id": cliente.id,
            "nombre": cliente.nombre,
            "puntos": cliente.puntos,
            "nivel": cliente.nivel,
            "descuento_aplicable_porcentaje": NIVELES.get(cliente.nivel, {}).get('descuento', 0),
            "fecha_registro": cliente.fecha_registro.isoformat() if cliente.fecha_registro else None
        }
    except Exception:
        raise ValueError(f"Cliente {id_cliente} no encontrado")


def get_ranking_clientes(limite=10):
    """Obtiene el ranking de clientes por puntos."""
    from apps.loyalty.models import ClienteLoyalty
    
    clientes = ClienteLoyalty.objects.order_by('-puntos')[:limite]
    
    ranking = []
    for i, cliente in enumerate(clientes, 1):
        ranking.append({
            "posicion": i,
            "id": cliente.id,
            "nombre": cliente.nombre,
            "puntos": cliente.puntos,
            "nivel": cliente.nivel
        })
    
    return {
        "fecha_consulta": datetime.now().isoformat(),
        "limite": limite,
        "ranking": ranking
    }
