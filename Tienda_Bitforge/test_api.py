import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BitForge.settings')
django.setup()

from gestion.services import hardware_api_service
from gestion.models import Producto, Categoria

# Probar la API de DummyJSON
print('=== TEST DummyJSON API ===')
productos = hardware_api_service.obtener_productos_dummyjson('laptops', 2)
for p in productos:
    print(f'{p["nombre"]}: ${p["precio"]} - {p["imagen_url"][:50]}...')

# Probar productos de hardware
print('\n=== TEST Hardware Products ===')
hw = hardware_api_service.obtener_productos_hardware('gpu', 2)
for p in hw:
    print(f'{p["nombre"]}: ${p["precio"]} - {p["imagen_url"][:50]}...')

# Probar importación
print('\n=== TEST Import ===')
creados, actualizados = hardware_api_service.importar_productos_api(Producto, Categoria, 'gpu', 2)
print(f'Creados: {creados}, Actualizados: {actualizados}')
print(f'\nTotal productos en BD: {Producto.objects.count()}')
