"""
Configuración de Celery para MicroERP.
Celery maneja tareas asíncronas y programación de tareas con Beat.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Configurar variables de entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('microerp')

# Cargar configuración desde settings de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en todas las apps instaladas
app.autodiscover_tasks()


# Tareas programadas con Celery Beat
app.conf.beat_schedule = {
    # Limpiar caché de analytics cada 24 horas
    'cleanup-analytics-cache': {
        'task': 'apps.analytics.tasks.cleanup_cache',
        'schedule': crontab(hour=3, minute=0),  # 3 AM diario
    },
    
    # Verificar vencimientos de productos diariamente
    'check-product-expirations': {
        'task': 'apps.purchasing.tasks.check_expirations',
        'schedule': crontab(hour=6, minute=0),  # 6 AM diario
    },
    
    # Generar sugerencias de pedidos semanalmente
    'generate-purchase-suggestions': {
        'task': 'apps.purchasing.tasks.generate_suggestions',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),  # Lunes 7 AM
    },
    
    # Actualizar KPIs del dashboard cada hora
    'update-dashboard-kpis': {
        'task': 'apps.analytics.tasks.update_dashboard_kpis',
        'schedule': crontab(minute=0),  # Cada hora en punto
    },
    
    # Enviar recordatorios de fiados por vencer (diario a las 8 AM)
    'remind-overdue-fiados': {
        'task': 'apps.finance.tasks.send_fiado_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
}


@app.task(bind=True)
def debug_task(self):
    """Tarea de prueba para verificar que Celery funciona correctamente."""
    print(f'Request: {self.request!r}')
    return 'Celery está funcionando correctamente'
