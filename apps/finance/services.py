from django.db import transaction
from django.db.models import Sum, Q, Coalesce
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from apps.finance.models import MovimientoFinanciero, Fiado
from apps.core.audit import AuditLogger

@transaction.atomic
def registrar_movimiento(tipo, monto, concepto, metodo, usuario=None):
    mov = MovimientoFinanciero.objects.create(
        tipo=tipo, monto=Decimal(str(monto)), concepto=concepto, metodo=metodo,
        usuario=usuario if usuario and hasattr(usuario, 'id') else None
    )
    AuditLogger.log("MOVIMIENTO_REGISTRADO", {"mov_id": mov.id, "tipo": tipo}, "SUCCESS", usuario)
    return {"id": mov.id, "fecha": mov.fecha.isoformat()}

@transaction.atomic
def registrar_fiado(id_cliente, monto, concepto, numero_wa, usuario=None):
    fiado = Fiado.objects.create(
        cliente_id=id_cliente, monto=Decimal(str(monto)), 
        fecha_vencimiento=datetime.now() + timedelta(days=30),
        estado='Pendiente', numero_whatsapp=numero_wa
    )
    AuditLogger.log("FIADO_REGISTRADO", {"fiado_id": fiado.id}, "SUCCESS", usuario)
    return {"id": fiado.id, "vencimiento": fiado.fecha_vencimiento.isoformat()}

@transaction.atomic
def registrar_pago_fiado(id_fiado, monto, metodo, usuario=None):
    fiado = Fiado.objects.select_for_update().get(id=id_fiado)
    MovimientoFinanciero.objects.create(
        tipo='Pago_Fiado', monto=Decimal(str(monto)), concepto=f"Pago fiado {id_fiado}", metodo=metodo
    )
    fiado.estado = 'Pagado'
    fiado.save()
    AuditLogger.log("PAGO_FIADO_REGISTRADO", {"fiado_id": id_fiado}, "SUCCESS", usuario)
    return {"id": fiado.id, "estado": fiado.estado}

@transaction.atomic
def registrar_pago_digital(id_cliente, monto, billetera, usuario=None):
    mov = MovimientoFinanciero.objects.create(
        tipo='Ingreso', monto=Decimal(str(monto)), concepto=f"Pago digital {billetera}", metodo=billetera
    )
    AuditLogger.log("PAGO_DIGITAL_REGISTRADO", {"mov_id": mov.id}, "SUCCESS", usuario)
    return {"id": mov.id, "fecha": mov.fecha.isoformat()}

@transaction.atomic(durable=True)
def get_flujo_caja(dias=30):
    desde = timezone.now() - timedelta(days=dias)
    
    # Aggregate en BD, no loops Python
    resultado = MovimientoFinanciero.objects.filter(fecha__gte=desde).aggregate(
        ingresos=Coalesce(Sum('monto', filter=Q(tipo='Ingreso')), Decimal('0')),
        egresos=Coalesce(Sum('monto', filter=Q(tipo='Egreso')), Decimal('0'))
    )
    ingresos = resultado['ingresos']
    egresos = resultado['egresos']
    neto = ingresos - egresos
    
    # Corregir typo: semafaro → semaforo
    semaforo = 'verde' if neto > 100000 else ('amarillo' if neto >= 0 else 'rojo')
    
    margen = (neto / ingresos * 100) if ingresos > 0 else 0
    
    return {
        "ingresos": str(ingresos), "egresos": str(egresos), "neto": str(neto),
        "semaforo": semaforo, "margen_porcentaje": round(margen, 2), "dias": dias
    }

def get_fiados_proximos_vencer():
    desde = datetime.now()
    hasta = datetime.now() + timedelta(days=7)
    fiados = Fiado.objects.filter(fecha_vencimiento__range=[desde, hasta], estado='Pendiente')
    return [{"id": f.id, "monto": str(f.monto), "vencimiento": f.fecha_vencimiento.isoformat()} for f in fiados]
