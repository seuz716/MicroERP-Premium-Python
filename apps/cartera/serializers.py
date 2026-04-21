from rest_framework import serializers

class ClienteCreditoSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    limite_credito = serializers.DecimalField(max_digits=10, decimal_places=2)

class FacturaSerializer(serializers.Serializer):
    id_cliente = serializers.CharField()
    items = serializers.ListField(child=serializers.DictField())
    fecha_vencimiento = serializers.DateField()

class PagoSerializer(serializers.Serializer):
    id_factura = serializers.CharField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
