"""
Admin del Core - Registro de modelos en el admin de Django.
"""
from django.contrib import admin
from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'accion', 'estado', 'usuario', 'ip_address')
    list_filter = ('estado', 'accion', 'timestamp')
    search_fields = ('accion', 'usuario__username', 'ip_address')
    readonly_fields = ('timestamp', 'usuario', 'accion', 'detalles', 'estado', 'ip_address', 'user_agent')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('timestamp', 'accion', 'estado')
        }),
        ('Usuario y Origen', {
            'fields': ('usuario', 'ip_address', 'user_agent')
        }),
        ('Detalles', {
            'fields': ('detalles',),
            'classes': ('collapse',)
        }),
    )
