from rest_framework import serializers

class MovimientoSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['Ingreso', 'Egreso', 'Pago_Fiado'])
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    concepto = serializers.CharField(max_length=200)
    metodo = serializers.CharField(max_length=50)

class FiadoSerializer(serializers.Serializer):
    id_cliente = serializers.CharField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    concepto = serializers.CharField(max_length=200)
    numero_wa = serializers.CharField(max_length=20)

class PagoFiadoSerializer(serializers.Serializer):
    id_fiado = serializers.CharField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    metodo = serializers.CharField(max_length=50)

class PagoDigitalSerializer(serializers.Serializer):
    id_cliente = serializers.CharField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    billetera = serializers.CharField(max_length=50)
