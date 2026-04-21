from rest_framework import serializers
from apps.core.validators import Validators

class VentaProcesarSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField())
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Carrito vacío")
        for item in value:
            if 'producto_id' not in item and 'id' not in item:
                raise serializers.ValidationError("Cada item debe tener producto_id")
            if 'cantidad' not in item:
                raise serializers.ValidationError("Cada item debe tener cantidad")
        return value

class VentaReadSerializer(serializers.Serializer):
    id_venta = serializers.CharField()
    total = serializers.CharField()
    fecha = serializers.DateTimeField()
    items = serializers.IntegerField()

class DashboardSerializer(serializers.Serializer):
    ventas_hoy = serializers.IntegerField()
    monto_ventas_hoy = serializers.CharField()
    utilidad_hoy = serializers.CharField()
    stock_total = serializers.IntegerField()
    valor_inventario = serializers.CharField()
