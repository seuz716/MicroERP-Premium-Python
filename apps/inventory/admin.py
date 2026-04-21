"""
Admin de Inventario.
"""
from django.contrib import admin
from apps.inventory.models import Producto, Entrada


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'stock', 'precio', 'created_at')
    search_fields = ('id', 'nombre')
    list_filter = ('stock', 'created_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'cantidad', 'costo', 'fecha')
    list_filter = ('fecha', 'producto')
    readonly_fields = ('fecha', 'created_at', 'updated_at')
