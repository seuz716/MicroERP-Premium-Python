"""
Modelos del Core - Registro de auditoría del sistema.
"""
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Registro de auditoría para todas las acciones del sistema.
    Almacena quién hizo qué, cuándo y con qué resultado.
    """
    
    class EstadoChoices(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Éxito'
        ERROR = 'ERROR', 'Error'
        WARNING = 'WARNING', 'Advertencia'
    
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuario'
    )
    accion = models.CharField(max_length=100, db_index=True, verbose_name='Acción')
    detalles = models.JSONField(default=dict, verbose_name='Detalles')
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.SUCCESS,
        db_index=True,
        verbose_name='Estado'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['accion']),
            models.Index(fields=['estado']),
            models.Index(fields=['usuario', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.accion} - {self.estado} ({self.timestamp})"
