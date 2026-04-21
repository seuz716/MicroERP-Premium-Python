from django.db import transaction
from decimal import Decimal
from datetime import datetime
from apps.cartera.models import ClienteCredito, Factura, Pago
from apps.core.audit import AuditLogger

@transaction.atomic
def crear_cliente_credito(nombre, limite_credito, usuario=None):
    cliente = ClienteCredito.objects.create(
        nombre=nombre,
        limite=Decimal(str(limite_credito)),
        saldo=Decimal('0'),
        activo=True
    )
    AuditLogger.log("CLIENTE_CREDITO_CREADO", {"cliente_id": cliente.id}, "SUCCESS", usuario)
    return {"id": cliente.id, "nombre": cliente.nombre, "limite": str(cliente.limite)}

@transaction.atomic
def registrar_factura(id_cliente, items, fecha_vencimiento, usuario=None):
    cliente = ClienteCredito.objects.select_for_update().get(id=id_cliente)
    monto_total = sum(Decimal(str(item.get('monto', 0))) for item in items)
    
    if cliente.saldo + monto_total > cliente.limite:
        raise ValueError("Supera límite de crédito")
    
    factura = Factura.objects.create(
        cliente=cliente,
        monto=monto_total,
        vencimiento=fecha_vencimiento,
        estado='PENDIENTE'
    )
    cliente.saldo += monto_total
    cliente.save()
    
    AuditLogger.log("FACTURA_REGISTRADA", {"factura_id": factura.id}, "SUCCESS", usuario)
    return {"id": factura.id, "monto": str(monto_total)}

@transaction.atomic
def registrar_pago(id_factura, monto, usuario=None):
    factura = Factura.objects.select_for_update().get(id=id_factura)
    pago = Pago.objects.create(factura=factura, monto=Decimal(str(monto)))
    
    factura.cliente.saldo -= Decimal(str(monto))
    factura.cliente.save()
    
    if factura.cliente.saldo <= 0:
        factura.estado = 'PAGADA'
    else:
        factura.estado = 'PAGADA_PARCIAL'
    factura.save()
    
    AuditLogger.log("PAGO_REGISTRADO", {"pago_id": pago.id}, "SUCCESS", usuario)
    return {"id": pago.id, "saldo_restante": str(factura.cliente.saldo)}

def get_cartera_status():
    clientes = list(ClienteCredito.objects.filter(activo=True).values())
    facturas_pendientes = Factura.objects.filter(estado='PENDIENTE').count()
    total_pendiente = sum(f.monto for f in Factura.objects.filter(estado='PENDIENTE'))
    return {
        "clientes_activos": len(clientes),
        "facturas_pendientes": facturas_pendientes,
        "total_pendiente": str(total_pendiente)
    }
