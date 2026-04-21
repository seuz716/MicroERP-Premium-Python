"""
Serializers de Inventario.
"""
from rest_framework import serializers
from apps.inventory.models import Producto, Entrada
from apps.core.validators import Validators


class ProductoWriteSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar productos."""
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'stock', 'precio']
    
    def validate_id(self, value):
        Validators.validate_id(value, 'ID Producto')
        return value
    
    def validate_nombre(self, value):
        Validators.validate_name(value, 'Nombre')
        return value
    
    def validate_precio(self, value):
        Validators.validate_price(value, 'Precio')
        return value
    
    def validate_stock(self, value):
        Validators.validate_stock(value, 'Stock')
        return value


class ProductoReadSerializer(serializers.ModelSerializer):
    """Serializer para leer productos."""
    
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'stock', 'precio', 'created_at', 'updated_at']


class EntradaWriteSerializer(serializers.ModelSerializer):
    """Serializer para crear entradas."""
    
    class Meta:
        model = Entrada
        fields = ['producto', 'cantidad', 'costo']
    
    def validate_cantidad(self, value):
        Validators.validate_quantity(value, 'Cantidad')
        return value
    
    def validate_costo(self, value):
        Validators.validate_price(value, 'Costo')
        return value


class EntradaReadSerializer(serializers.ModelSerializer):
    """Serializer para leer entradas."""
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    
    class Meta:
        model = Entrada
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'costo', 'fecha', 'created_at']
