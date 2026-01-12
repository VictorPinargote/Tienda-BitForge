# 🎮 BitForge - E-commerce de Hardware

Sistema de gestión de ventas de hardware con Django, especializado en componentes de PC, kits de actualización y equipos armados.

## 📋 Características

### Para Clientes
- ✅ Catálogo de productos con filtros y búsqueda
- ✅ Carrito de compras con validación de stock
- ✅ Sistema de solicitudes para productos agotados
- ✅ Registro e inicio de sesión

### Para Administradores
- ✅ Panel de control con estadísticas
- ✅ Gestión de solicitudes de clientes
- ✅ Sincronización de precios via API externa

### Para Bodegueros
- ✅ Panel de gestión de stock
- ✅ Actualización de inventario
- ✅ Marcado de solicitudes como completadas

## 🔧 Tecnologías

- **Backend:** Django 6.0
- **Frontend:** Bootstrap 5
- **Base de datos:** SQLite
- **APIs:** FakeStore API (demo)

## 🚀 Instalación

```bash
# Clonar repositorio
git clone <url-del-repo>
cd Tienda_Bitforge

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows

# Instalar dependencias
pip install django requests

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

## 📁 Estructura del Proyecto

```
Tienda_Bitforge/
├── BitForge/          # Configuración del proyecto
│   ├── settings.py
│   └── urls.py
├── gestion/           # App principal
│   ├── models.py      # Categoria, Proveedor, Producto, Solicitud, CarritoItem
│   ├── views.py       # Todas las vistas
│   ├── urls.py        # Rutas de la app
│   └── templates/     # Templates HTML
└── manage.py
```

## 👥 Roles de Usuario

| Rol | Permisos |
|-----|----------|
| Cliente | Ver catálogo, carrito, solicitudes propias |
| Staff | Todo lo anterior + panel admin, gestionar solicitudes |
| Superuser | Todo + Django Admin |

## 📱 URLs Principales

| URL | Descripción |
|-----|-------------|
| `/` | Página principal |
| `/catalogo/` | Catálogo con filtros |
| `/carrito/` | Ver carrito |
| `/mis-solicitudes/` | Solicitudes del cliente |
| `/admin/panel/` | Panel administrativo |
| `/admin/solicitudes/` | Gestionar solicitudes |
| `/admin/stock/` | Gestionar inventario |

## 🔄 Flujo de Solicitudes

1. **Cliente** solicita producto agotado
2. **Admin** visualiza la solicitud
3. **Bodeguero** recibe mercancía y actualiza stock
4. **Sistema** marca solicitud como completada automáticamente

## 📦 Modelos

- **Categoria:** Clasificación de productos
- **Proveedor:** Origen de la mercancía
- **Producto:** Items del catálogo con stock y precios
- **Solicitud:** Pedidos especiales de clientes
- **CarritoItem:** Items en el carrito de compras

## 🎨 Diseño

Tema oscuro estilo "gaming" con:
- Colores neón (verde #00ff88, azul #00ccff)
- Fuente Orbitron para títulos
- Efecto glassmorphism en tarjetas
- Animaciones hover

---

Desarrollado con Django 🐍
