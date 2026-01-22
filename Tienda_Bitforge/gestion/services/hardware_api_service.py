"""
Servicio de API de Hardware para BitForge
Combina DummyJSON (productos de tecnología) + Pixabay (imágenes de hardware)
APIs REALES que funcionan sin bloqueos
"""
import os
import re
import requests
from decimal import Decimal
import hashlib
import random

# API Keys y URLs
DUMMYJSON_BASE = 'https://dummyjson.com'
PIXABAY_API_KEY = '54315660-127b2955583a72e4ac73f6889'  # API Key real de Pixabay
PIXABAY_BASE = 'https://pixabay.com/api/'

# Headers para requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

# Mapeo de categorías DummyJSON a categorías BitForge (solo PCs)
CATEGORIA_MAP = {
    'laptops': 'PCs Armadas',
}

# Productos de hardware personalizados (basados en datos reales)
HARDWARE_PRODUCTS = {
    'cpu': [
        {'nombre': 'Intel Core i9-14900K', 'precio': 589.99, 'specs': '24 núcleos, 6.0GHz, LGA1700'},
        {'nombre': 'Intel Core i7-14700K', 'precio': 409.99, 'specs': '20 núcleos, 5.6GHz, LGA1700'},
        {'nombre': 'Intel Core i5-14600K', 'precio': 319.99, 'specs': '14 núcleos, 5.3GHz, LGA1700'},
        {'nombre': 'AMD Ryzen 9 7950X3D', 'precio': 699.99, 'specs': '16 núcleos, 5.7GHz, 128MB 3D V-Cache'},
        {'nombre': 'AMD Ryzen 7 7800X3D', 'precio': 449.99, 'specs': '8 núcleos, 5.0GHz, 96MB 3D V-Cache'},
        {'nombre': 'AMD Ryzen 5 7600X', 'precio': 229.99, 'specs': '6 núcleos, 5.3GHz, AM5'},
    ],
    'gpu': [
        {'nombre': 'NVIDIA RTX 4090 24GB', 'precio': 1599.99, 'specs': '24GB GDDR6X, 16384 CUDA Cores'},
        {'nombre': 'NVIDIA RTX 4080 Super 16GB', 'precio': 999.99, 'specs': '16GB GDDR6X, 10240 CUDA Cores'},
        {'nombre': 'NVIDIA RTX 4070 Ti Super', 'precio': 799.99, 'specs': '16GB GDDR6X, 8448 CUDA Cores'},
        {'nombre': 'NVIDIA RTX 4070 12GB', 'precio': 599.99, 'specs': '12GB GDDR6X, 5888 CUDA Cores'},
        {'nombre': 'AMD Radeon RX 7900 XTX', 'precio': 949.99, 'specs': '24GB GDDR6, RDNA 3'},
        {'nombre': 'AMD Radeon RX 7900 XT', 'precio': 749.99, 'specs': '20GB GDDR6, RDNA 3'},
    ],
    'ram': [
        {'nombre': 'Corsair Vengeance DDR5 32GB', 'precio': 149.99, 'specs': '2x16GB DDR5-6000 CL36'},
        {'nombre': 'G.Skill Trident Z5 RGB 64GB', 'precio': 299.99, 'specs': '2x32GB DDR5-6400 CL32'},
        {'nombre': 'Kingston Fury Beast 32GB', 'precio': 119.99, 'specs': '2x16GB DDR5-5600 CL40'},
        {'nombre': 'TeamGroup T-Force Delta 32GB', 'precio': 139.99, 'specs': '2x16GB DDR5-6000 RGB'},
        {'nombre': 'Corsair Dominator Platinum 64GB', 'precio': 349.99, 'specs': '2x32GB DDR5-6600 CL32'},
    ],
    'ssd': [
        {'nombre': 'Samsung 990 Pro 2TB NVMe', 'precio': 179.99, 'specs': 'PCIe 4.0, 7450MB/s lectura'},
        {'nombre': 'WD Black SN850X 2TB', 'precio': 159.99, 'specs': 'PCIe 4.0, 7300MB/s lectura'},
        {'nombre': 'Seagate FireCuda 530 2TB', 'precio': 189.99, 'specs': 'PCIe 4.0, 7300MB/s lectura'},
        {'nombre': 'Crucial T700 2TB', 'precio': 279.99, 'specs': 'PCIe 5.0, 12400MB/s lectura'},
        {'nombre': 'Kingston KC3000 2TB', 'precio': 149.99, 'specs': 'PCIe 4.0, 7000MB/s lectura'},
    ],
    'motherboard': [
        {'nombre': 'ASUS ROG Maximus Z790 Hero', 'precio': 629.99, 'specs': 'LGA1700, DDR5, PCIe 5.0'},
        {'nombre': 'MSI MEG Z790 ACE', 'precio': 549.99, 'specs': 'LGA1700, DDR5, WiFi 7'},
        {'nombre': 'Gigabyte Z790 AORUS Master', 'precio': 499.99, 'specs': 'LGA1700, DDR5, Thunderbolt 4'},
        {'nombre': 'ASUS ROG Crosshair X670E Hero', 'precio': 699.99, 'specs': 'AM5, DDR5, PCIe 5.0'},
        {'nombre': 'MSI MEG X670E ACE', 'precio': 599.99, 'specs': 'AM5, DDR5, WiFi 6E'},
    ],
}

# Términos de búsqueda optimizados para Pixabay
PIXABAY_SEARCH_TERMS = {
    'cpu': 'computer processor cpu chip',
    'gpu': 'graphics card gpu nvidia',
    'ram': 'computer memory ram ddr',
    'ssd': 'ssd hard drive storage',
    'motherboard': 'motherboard computer circuit board',
}


def obtener_imagen_pixabay(tipo_hardware):
    """
    Obtiene una imagen REAL de Pixabay relacionada con el tipo de hardware.
    Usa la API de Pixabay con una API key válida.
    """
    try:
        termino = PIXABAY_SEARCH_TERMS.get(tipo_hardware, 'computer hardware')
        params = {
            'key': PIXABAY_API_KEY,
            'q': termino,
            'image_type': 'photo',
            'per_page': 20,
            'safesearch': 'true',
            'orientation': 'horizontal',
        }
        response = requests.get(PIXABAY_BASE, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('hits') and len(data['hits']) > 0:
            # Seleccionar imagen aleatoria de los resultados
            hit = random.choice(data['hits'][:10])
            return hit.get('webformatURL') or hit.get('previewURL')
    except Exception as e:
        print(f"Error obteniendo imagen de Pixabay: {e}")
    
    # Fallback a imágenes de Unsplash si Pixabay falla
    return obtener_imagen_fallback(tipo_hardware)


def obtener_imagen_fallback(tipo_hardware):
    """Imágenes de respaldo de Unsplash si Pixabay falla"""
    imagenes_fallback = {
        'cpu': 'https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400',
        'gpu': 'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400',
        'ram': 'https://images.unsplash.com/photo-1562976540-1502c2145186?w=400',
        'ssd': 'https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400',
        'motherboard': 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400',
    }
    return imagenes_fallback.get(tipo_hardware, imagenes_fallback['cpu'])


def obtener_productos_dummyjson(categoria='laptops', limite=10):
    """
    Obtiene productos de tecnología desde DummyJSON API.
    Categorías disponibles: laptops, smartphones, tablets, mobile-accessories
    """
    productos = []
    try:
        url = f"{DUMMYJSON_BASE}/products/category/{categoria}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        for item in data.get('products', [])[:limite]:
            productos.append({
                'nombre': item['title'],
                'descripcion': item['description'],
                'precio': Decimal(str(item['price'])),
                'stock': item.get('stock', 10),
                'imagen_url': item.get('thumbnail') or (item['images'][0] if item.get('images') else ''),
                'categoria_local': CATEGORIA_MAP.get(categoria, 'Componentes'),
                'rating': item.get('rating', 4.0),
                'brand': item.get('brand', ''),
            })
    except Exception as e:
        print(f"Error obteniendo productos de DummyJSON: {e}")
    
    return productos


def obtener_productos_hardware(tipo='cpu', limite=5):
    """
    Obtiene productos de hardware con datos reales e imágenes de Pixabay.
    Tipos: cpu, gpu, ram, ssd, motherboard
    """
    productos = []
    productos_base = HARDWARE_PRODUCTS.get(tipo, [])[:limite]
    
    # Categorías locales por tipo
    categorias_locales = {
        'cpu': 'Procesadores',
        'gpu': 'Tarjetas Gráficas',
        'ram': 'Memoria RAM',
        'ssd': 'Almacenamiento',
        'motherboard': 'Motherboards',
    }
    
    for producto in productos_base:
        # Obtener imagen REAL de Pixabay
        imagen_url = obtener_imagen_pixabay(tipo)
        
        productos.append({
            'nombre': producto['nombre'],
            'descripcion': producto['specs'],
            'precio': Decimal(str(producto['precio'])),
            'stock': random.randint(5, 50),
            'imagen_url': imagen_url,
            'categoria_local': categorias_locales.get(tipo, 'Componentes'),
        })
    
    return productos


def importar_productos_api(Producto, Categoria, tipo='cpu', limite=5):
    """
    Importa productos de hardware a Django usando las APIs.
    
    Args:
        Producto: Modelo Producto de Django
        Categoria: Modelo Categoria de Django
        tipo: Tipo de producto (cpu, gpu, ram, ssd, motherboard, laptops)
        limite: Cantidad máxima de productos
    
    Returns:
        Tuple (creados, actualizados)
    """
    creados = 0
    actualizados = 0
    
    # Obtener productos según el tipo
    if tipo in ['laptops', 'smartphones', 'tablets']:
        productos_data = obtener_productos_dummyjson(tipo, limite)
    else:
        productos_data = obtener_productos_hardware(tipo, limite)
    
    for data in productos_data:
        try:
            # Obtener o crear categoría
            categoria_nombre = data.get('categoria_local', 'Componentes')
            categoria, _ = Categoria.objects.get_or_create(
                nombre=categoria_nombre,
                defaults={'descripcion': f'Productos de {categoria_nombre}'}
            )
            
            # Crear o actualizar producto
            producto, created = Producto.objects.update_or_create(
                nombre=data['nombre'],
                defaults={
                    'descripcion': data.get('descripcion', ''),
                    'precio': data.get('precio', Decimal('0')),
                    'stock': data.get('stock', 10),
                    'imagen_url': data.get('imagen_url', ''),
                    'categoria': categoria,
                    'tipo': 'componente',
                    'disponible': True,
                }
            )
            
            if created:
                creados += 1
            else:
                actualizados += 1
                
        except Exception as e:
            print(f"Error importando {data.get('nombre', 'desconocido')}: {e}")
            continue
    
    return creados, actualizados


def actualizar_precios_api(Producto):
    """
    Actualiza precios de productos existentes con variaciones realistas.
    Simula fluctuaciones del mercado basadas en demanda.
    """
    actualizados = 0
    
    for producto in Producto.objects.filter(disponible=True):
        try:
            # Fluctuación realista: -3% a +5%
            factor = Decimal(str(random.uniform(0.97, 1.05)))
            nuevo_precio = producto.precio * factor
            producto.precio = round(nuevo_precio, 2)
            producto.save()
            actualizados += 1
        except Exception as e:
            print(f"Error actualizando precio de {producto.nombre}: {e}")
    
    return actualizados


def buscar_productos_api(termino, limite=10):
    """
    Busca productos en DummyJSON por término de búsqueda.
    """
    productos = []
    try:
        url = f"{DUMMYJSON_BASE}/products/search?q={termino}&limit={limite}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        for item in data.get('products', []):
            productos.append({
                'nombre': item['title'],
                'descripcion': item['description'],
                'precio': Decimal(str(item['price'])),
                'imagen_url': item.get('thumbnail', ''),
                'categoria': item.get('category', ''),
            })
    except Exception as e:
        print(f"Error buscando productos: {e}")
    
    return productos
