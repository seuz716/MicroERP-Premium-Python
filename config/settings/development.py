"""
Settings para desarrollo local.
Extiende la configuración base con opciones específicas para desarrollo.
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Django Debug Toolbar (opcional para desarrollo)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Email backend para desarrollo (consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache con timeout menor para desarrollo
CACHES['default']['TIMEOUT'] = 60

# Logging más detallado en desarrollo
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

# CORS para desarrollo
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
]

# REST Framework - más permisos en desarrollo
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.AllowAny',
]
