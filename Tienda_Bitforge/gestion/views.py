from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm #Formulario para creación de usuario
from django.contrib import messages #Mensajes de confirmación
from .models import Producto, CarritoItem, Solicitud, Categoria
from django.contrib.admin.views.decorators import staff_member_required
import requests

# Vista principal - Página de inicio
def home(request):
    #Muestra la página principal con el catálogo de productos.
    productos = Producto.objects.filter(disponible=True)
    return render(request, 'index.html', {'productos': productos}) #renderiza el template y lo devuelve en la página web


# Vista de registro
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente')
            return redirect('login')
        else:
            messages.error(request, 'Error al crear el usuario')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})

# Vista del carrito
@login_required
def ver_carrito(request):
    items = CarritoItem.objects.filter(usuario=request.user)
    total = sum(item.subtotal() for item in items)
    return render(request, 'carrito.html', {'items': items, 'total': total})

# Vista de agregar al carrito
@login_required
def agregar_carrito(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    item, created = CarritoItem.objects.get_or_create(
        usuario=request.user,
        producto=producto,
        defaults={'cantidad': 1}
    )
    
    if not created:
        item.cantidad += 1
        item.save()
    
    messages.success(request, f'{producto.nombre} agregado al carrito')
    return redirect('home')

# Vista de eliminar del carrito
@login_required
def eliminar_carrito(request, item_id):
    item = CarritoItem.objects.get(id=item_id, usuario=request.user)
    item.delete()
    messages.success(request, 'Producto eliminado del carrito')
    return redirect('ver_carrito')

# Vista de actualizar cantidad
@login_required
def actualizar_cantidad(request, item_id):
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        item = CarritoItem.objects.get(id=item_id, usuario=request.user)
        if cantidad > 0:
            item.cantidad = cantidad
            item.save()
        else:
            item.delete()
    return redirect('ver_carrito')

# Vista de crear solicitud
@login_required
def crear_solicitud(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    
    if request.method == 'POST':
        nota = request.POST.get('nota', '')
        cantidad = int(request.POST.get('cantidad', 1))
        
        Solicitud.objects.create(
            cliente=request.user,
            producto=producto,
            cantidad=cantidad,
            nota_cliente=nota
        )
        messages.success(request, f'Solicitud de {producto.nombre} enviada correctamente')
        return redirect('mis_solicitudes')
    
    return render(request, 'crear_solicitud.html', {'producto': producto})

# Vista de mis solicitudes
@login_required
def mis_solicitudes(request):
    solicitudes = Solicitud.objects.filter(cliente=request.user)
    return render(request, 'mis_solicitudes.html', {'solicitudes': solicitudes})

# Vista de solicitudes admin
@staff_member_required
def ver_solicitudes_admin(request):
    solicitudes = Solicitud.objects.all()
    return render(request, 'admin/solicitudes_admin.html', {'solicitudes': solicitudes})

# Vista de marcar solicitud como completada
@staff_member_required
def marcar_completada(request, solicitud_id):
    solicitud = Solicitud.objects.get(id=solicitud_id)
    solicitud.estado = 'completada'
    solicitud.save()
    
    # Aumentar stock del producto
    solicitud.producto.stock += solicitud.cantidad
    solicitud.producto.save()
    
    messages.success(request, f'Solicitud #{solicitud.id} completada y stock actualizado')
    return redirect('solicitudes_admin')

# Vista de importar precios
def importar_precios(request):
    url = "https://fakestoreapi.com/products?limit=8"
    
    try:
        response = requests.get(url, timeout=10)
        productos_api = response.json()
        
        from .models import Categoria
        categoria, _ = Categoria.objects.get_or_create(
            nombre='Importados',
            defaults={'descripcion': 'Productos importados via API'}
        )
        
        for item in productos_api:
            Producto.objects.update_or_create(
                nombre=item['title'][:50],
                defaults={
                    'descripcion': item['description'],
                    'precio': item['price'],
                    'stock': 10,
                    'imagen_url': item['image'],
                    'categoria': categoria,
                    'disponible': True
                }
            )
        
        messages.success(request, f'{len(productos_api)} productos sincronizados desde API')
    except Exception as e:
        messages.error(request, f'Error al importar: {str(e)}')
    
    return redirect('home')

# Vista del detalle del producto
def detalle_producto(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    relacionados = Producto.objects.filter(categoria=producto.categoria).exclude(id=producto_id)[:4]
    return render(request, 'detalle_producto.html', {
        'producto': producto,
        'relacionados': relacionados
    })

# Vista del catalogo
def catalogo(request):
    productos = Producto.objects.filter(disponible=True)
    categorias = Categoria.objects.all()
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('q')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)
    
    return render(request, 'catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_actual': categoria_id,
        'busqueda': busqueda
    })

# Vista de gestion de stock
@staff_member_required
def gestion_stock(request):
    productos = Producto.objects.all().order_by('stock')
    return render(request, 'admin/gestion_stock.html', {'productos': productos})

# Vista de actualizar stock
@staff_member_required
def actualizar_stock(request, producto_id):
    if request.method == 'POST':
        producto = Producto.objects.get(id=producto_id)
        nuevo_stock = int(request.POST.get('stock', 0))
        producto.stock = nuevo_stock
        producto.save()
        messages.success(request, f'Stock de {producto.nombre} actualizado a {nuevo_stock}')
    return redirect('gestion_stock')

#Vista del panel admin
@staff_member_required  
def panel_admin(request):
    from django.db.models import Sum
    
    total_productos = Producto.objects.count()
    productos_agotados = Producto.objects.filter(stock=0).count()
    solicitudes_pendientes = Solicitud.objects.filter(estado='pendiente').count()
    total_ventas = CarritoItem.objects.aggregate(Sum('cantidad'))['cantidad__sum'] or 0
    
    return render(request, 'admin/panel_admin.html', {
        'total_productos': total_productos,
        'productos_agotados': productos_agotados,
        'solicitudes_pendientes': solicitudes_pendientes,
        'total_ventas': total_ventas
    })

# Vista de agregar al carrito
@login_required
def agregar_carrito(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    # Validar stock
    if producto.stock <= 0:
        messages.error(request, 'Este producto no tiene stock disponible')
        return redirect('home')
    
    item, created = CarritoItem.objects.get_or_create(
        usuario=request.user,
        producto=producto,
        defaults={'cantidad': 1}
    )
    
    if not created:
        if item.cantidad < producto.stock:
            item.cantidad += 1
            item.save()
        else:
            messages.warning(request, 'No hay suficiente stock')
            return redirect('home')
    
    messages.success(request, f'{producto.nombre} agregado al carrito')
    return redirect('home')

# Create your views here.
