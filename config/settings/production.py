"""
Settings para producción.
Extiende la configuración base con opciones específicas para producción.
IMPORTANTE: Nunca ejecutar con DEBUG=True en producción.
"""
from .base import *
from django.core.exceptions import ImproperlyConfigured

# SECURITY WARNING: don't run with debug turned on in production!
if DEBUG:
    raise ImproperlyConfigured(
        "No se puede ejecutar en producción con DEBUG=True. "
        "Establece DEBUG=False en las variables de entorno."
    )

# Security settings para producción
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Allowed hosts debe estar configurado en el entorno
if not config('ALLOWED_HOSTS', default=''):
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS debe estar configurado en producción"
    )

# Static files con CDN (opcional)
# STATIC_URL = 'https://cdn.tudominio.com/static/'

# Email backend para producción
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Cache con timeout mayor para producción
CACHES['default']['TIMEOUT'] = 600  # 10 minutos

# Logging más conservador en producción
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps']['level'] = 'INFO'

# REST Framework - autenticación requerida en producción
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.IsAuthenticated',
]

# Rate limiting para producción
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
}
