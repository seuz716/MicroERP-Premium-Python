"""
Modelos de Inventario - Productos y Entradas.
"""
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.core.validators import Validators
from apps.core.cache import ProductCache


class Producto(models.Model):
    """
    Producto del inventario.
    PK: ID personalizado con formato alfanumérico (ej: PROD_001)
    """
    id = models.CharField(
        primary_key=True,
        max_length=20,
        unique=True,
        verbose_name='ID Producto'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    stock = models.IntegerField(default=0, verbose_name='Stock')
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Precio'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    
    class Meta:
        ordering = ['nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['stock']),
        ]
    
    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"
    
    def clean(self):
        Validators.validate_id(self.id, 'ID Producto')
        Validators.validate_name(self.nombre, 'Nombre')
        Validators.validate_price(self.precio, 'Precio')
        Validators.validate_stock(self.stock, 'Stock')


class Entrada(models.Model):
    """
    Entrada de inventario (compra o reposición).
    """
    id = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='entradas',
        verbose_name='Producto'
    )
    cantidad = models.IntegerField(verbose_name='Cantidad')
    costo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Costo Unitario'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Entrada'
        verbose_name_plural = 'Entradas'
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['producto', 'fecha']),
        ]
    
    def __str__(self):
        return f"Entrada {self.producto.nombre} - {self.cantidad} unidades ({self.fecha.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Validar antes de guardar
        Validators.validate_quantity(self.cantidad, 'Cantidad')
        Validators.validate_price(self.costo, 'Costo')
        super().save(*args, **kwargs)


# Signals para invalidación automática del caché de productos
@receiver([post_save, post_delete], sender=Producto)
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalida el caché de un producto cuando se guarda o elimina."""
    ProductCache.invalidate(instance.id)
