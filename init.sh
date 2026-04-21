#!/bin/bash
# init.sh - Script de inicialización del MicroERP
# Ejecuta migraciones y crea superusuario automáticamente

set -e

echo "🚀 Iniciando MicroERP..."

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 5

# Ejecutar migraciones
echo "📦 Ejecutando migraciones de base de datos..."
python manage.py makemigrations
python manage.py migrate

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superusuario si no existe
echo "👤 Creando superusuario por defecto..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@microerp.com',
        password='admin123',
        first_name='Administrador',
        last_name='MicroERP'
    )
    print('✅ Superusuario creado: admin / admin123')
else:
    print('ℹ️  El superusuario ya existe')
EOF

# Ejecutar script de datos iniciales (si existe)
if [ -f "scripts/seed_data.py" ]; then
    echo "🌱 Cargando datos iniciales..."
    python scripts/seed_data.py
fi

echo "✅ MicroERP iniciado exitosamente!"
echo "📍 API disponible en: http://localhost:8000/api/v1/"
echo "🔧 Admin Django disponible en: http://localhost:8000/admin/"
echo "👤 Credenciales: admin / admin123"
