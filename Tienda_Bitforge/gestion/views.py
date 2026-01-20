from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from .models import (
    Producto, CarritoItem, Solicitud, Categoria, 
    Pedido, PedidoItem, Resena, ListaDeseos, 
    Cupon, PerfilUsuario, SuscripcionNewsletter, ProductoComparado
)
from django.contrib.admin.views.decorators import staff_member_required
import requests
import random
from decimal import Decimal

# Vista principal - Página de inicio
def home(request):
    productos = Producto.objects.filter(disponible=True)
    return render(request, 'index.html', {'productos': productos})


# Vista de registro con roles
CODIGO_BODEGA_SECRETO = "bitforge2024"  # Código que solo tú conoces

def registro(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        rol = request.POST.get('rol', 'cliente')
        codigo_bodega = request.POST.get('codigo_bodega', '')
        
        # Validaciones
        if not username or not password1:
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'registration/registro.html')
        
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'registration/registro.html')
        
        if len(password1) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            return render(request, 'registration/registro.html')
        
        # Verificar si el usuario ya existe
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
            return render(request, 'registration/registro.html')
        
        # Si es bodeguero, verificar código
        if rol == 'bodeguero':
            if codigo_bodega != CODIGO_BODEGA_SECRETO:
                messages.error(request, '❌ Código de bodega incorrecto. Contacta al administrador.')
                return render(request, 'registration/registro.html')
        
        # Crear usuario
        user = User.objects.create_user(username=username, password=password1)
        
        # Si es bodeguero, hacerlo staff
        if rol == 'bodeguero':
            user.is_staff = True
            user.save()
            messages.success(request, '✅ Cuenta de Bodeguero creada correctamente')
        else:
            messages.success(request, '✅ Cuenta de Cliente creada correctamente')
        
        return redirect('login')
    
    return render(request, 'registration/registro.html')

# Vista del carrito
@login_required
def ver_carrito(request):
    items = CarritoItem.objects.filter(usuario=request.user).select_related('producto')
    subtotal = sum(item.subtotal() for item in items)
    total_items = sum(item.cantidad for item in items)
    
    # Verificar cupón en sesión
    descuento = Decimal('0')
    cupon = None
    cupon_codigo = request.session.get('cupon_codigo')
    
    if cupon_codigo:
        try:
            cupon = Cupon.objects.get(codigo=cupon_codigo)
            if cupon.esta_vigente() and subtotal >= cupon.compra_minima:
                descuento = subtotal * Decimal(cupon.descuento_porcentaje) / 100
                if cupon.descuento_maximo and descuento > cupon.descuento_maximo:
                    descuento = cupon.descuento_maximo
        except Cupon.DoesNotExist:
            del request.session['cupon_codigo']
    
    total_final = subtotal - descuento
    
    # Productos sugeridos (excluir los que ya están en carrito)
    productos_en_carrito = [item.producto_id for item in items]
    sugerencias = Producto.objects.filter(
        disponible=True, 
        stock__gt=0
    ).exclude(id__in=productos_en_carrito)[:4]
    
    return render(request, 'carrito.html', {
        'items': items,
        'total': subtotal,
        'total_items': total_items,
        'cupon': cupon,
        'descuento': descuento,
        'total_final': total_final,
        'sugerencias': sugerencias
    })

# Vista de agregar al carrito (CON VALIDACIÓN DE STOCK)
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

# Vista de finalizar compra (CHECKOUT)
@login_required
def finalizar_compra(request):
    items = CarritoItem.objects.filter(usuario=request.user)
    
    if not items:
        messages.error(request, 'Tu carrito está vacío')
        return redirect('ver_carrito')
    
    # Validar stock antes de procesar
    for item in items:
        if item.producto.stock < item.cantidad:
            messages.error(request, f'No hay suficiente stock de {item.producto.nombre}')
            return redirect('ver_carrito')
    
    # Procesar compra - restar stock
    for item in items:
        item.producto.stock -= item.cantidad
        item.producto.save()
    
    # Limpiar carrito
    items.delete()
    
    messages.success(request, '🎉 ¡Compra realizada con éxito! Tu pedido está en proceso.')
    return redirect('home')

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

# Vista de importar precios (SOLO ACTUALIZA PRECIOS, NO CREA PRODUCTOS)
def importar_precios(request):
    endpoint = 'https://fakestoreapi.com/products/category/electronics'
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Solo actualizamos precios de productos EXISTENTES
        productos_locales = Producto.objects.all()
        count = 0
        
        for prod in productos_locales:
            precio_ref = random.choice(data)['price']
            prod.precio = round(precio_ref * 10, 2)
            prod.save()
            count += 1
            
        messages.success(request, f'✅ Conexión con Proveedores Globales. {count} precios actualizados en tiempo real.')
        
    except Exception as e:
        messages.error(request, f'❌ Error de conexión con proveedores: {str(e)}')
        
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
    
    # Filtros básicos
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('q')
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)
    
    # Filtros de precio
    precio_min = request.GET.get('precio_min')
    precio_max = request.GET.get('precio_max')
    
    if precio_min:
        try:
            productos = productos.filter(precio__gte=Decimal(precio_min))
        except:
            pass
    if precio_max:
        try:
            productos = productos.filter(precio__lte=Decimal(precio_max))
        except:
            pass
    
    # Solo con stock
    if request.GET.get('solo_stock'):
        productos = productos.filter(stock__gt=0)
    
    # Ordenamiento
    orden = request.GET.get('orden')
    if orden == 'precio_asc':
        productos = productos.order_by('precio')
    elif orden == 'precio_desc':
        productos = productos.order_by('-precio')
    elif orden == 'nombre':
        productos = productos.order_by('nombre')
    else:
        productos = productos.order_by('-fecha_creacion')
    
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

# Vista del panel admin
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

# Vista para cargar productos de hardware iniciales
@staff_member_required
def cargar_productos_demo(request):
    # Crear categorías de hardware
    cat_gpu, _ = Categoria.objects.get_or_create(nombre='Tarjetas Gráficas', defaults={'descripcion': 'GPUs de alto rendimiento'})
    cat_cpu, _ = Categoria.objects.get_or_create(nombre='Procesadores', defaults={'descripcion': 'CPUs Intel y AMD'})
    cat_ram, _ = Categoria.objects.get_or_create(nombre='Memoria RAM', defaults={'descripcion': 'Módulos DDR4 y DDR5'})
    cat_ssd, _ = Categoria.objects.get_or_create(nombre='Almacenamiento', defaults={'descripcion': 'SSD y HDD'})
    cat_kit, _ = Categoria.objects.get_or_create(nombre='Kits', defaults={'descripcion': 'Combos de actualización'})
    cat_pc, _ = Categoria.objects.get_or_create(nombre='PCs Armadas', defaults={'descripcion': 'Equipos listos para usar'})
    
    # Productos de hardware reales
    productos_hardware = [
        {'nombre': 'NVIDIA RTX 4090 24GB', 'precio': 1599.99, 'stock': 5, 'categoria': cat_gpu, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400'},
        {'nombre': 'NVIDIA RTX 4070 Ti 12GB', 'precio': 799.99, 'stock': 8, 'categoria': cat_gpu, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400'},
        {'nombre': 'AMD Radeon RX 7900 XTX', 'precio': 999.99, 'stock': 3, 'categoria': cat_gpu, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400'},
        {'nombre': 'Intel Core i9-14900K', 'precio': 589.99, 'stock': 10, 'categoria': cat_cpu, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1555618568-9b1686616012?w=400'},
        {'nombre': 'Intel Core i7-14700K', 'precio': 409.99, 'stock': 12, 'categoria': cat_cpu, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1555618568-9b1686616012?w=400'},
        {'nombre': 'AMD Ryzen 9 7950X3D', 'precio': 699.99, 'stock': 4, 'categoria': cat_cpu, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1555618568-9b1686616012?w=400'},
        {'nombre': 'AMD Ryzen 7 7800X3D', 'precio': 449.99, 'stock': 7, 'categoria': cat_cpu, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1555618568-9b1686616012?w=400'},
        {'nombre': 'Corsair Vengeance DDR5 32GB', 'precio': 149.99, 'stock': 20, 'categoria': cat_ram, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1562976540-1502c2145186?w=400'},
        {'nombre': 'G.Skill Trident Z5 64GB DDR5', 'precio': 299.99, 'stock': 6, 'categoria': cat_ram, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1562976540-1502c2145186?w=400'},
        {'nombre': 'Samsung 990 Pro 2TB NVMe', 'precio': 179.99, 'stock': 15, 'categoria': cat_ssd, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400'},
        {'nombre': 'WD Black SN850X 1TB', 'precio': 89.99, 'stock': 25, 'categoria': cat_ssd, 'tipo': 'componente', 'imagen_url': 'https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400'},
        {'nombre': 'Kit Gamer AMD Ryzen 7 + B650', 'precio': 699.99, 'stock': 3, 'categoria': cat_kit, 'tipo': 'kit', 'imagen_url': 'https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400'},
        {'nombre': 'Kit Intel i5 + Z790 + 32GB', 'precio': 849.99, 'stock': 0, 'categoria': cat_kit, 'tipo': 'kit', 'imagen_url': 'https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=400'},
        {'nombre': 'PC Gamer BitForge TITAN', 'precio': 2499.99, 'stock': 2, 'categoria': cat_pc, 'tipo': 'pc_armada', 'imagen_url': 'https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=400'},
        {'nombre': 'PC Gamer BitForge PHOENIX', 'precio': 1799.99, 'stock': 4, 'categoria': cat_pc, 'tipo': 'pc_armada', 'imagen_url': 'https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=400'},
        {'nombre': 'PC Workstation BitForge PRO', 'precio': 3299.99, 'stock': 1, 'categoria': cat_pc, 'tipo': 'pc_armada', 'imagen_url': 'https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=400'},
    ]
    
    count = 0
    for p in productos_hardware:
        Producto.objects.update_or_create(
            nombre=p['nombre'],
            defaults={
                'descripcion': f"Hardware de alto rendimiento - {p['categoria'].nombre}",
                'precio': p['precio'],
                'stock': p['stock'],
                'categoria': p['categoria'],
                'tipo': p['tipo'],
                'imagen_url': p['imagen_url'],
                'disponible': True
            }
        )
        count += 1
    
    messages.success(request, f'✅ {count} productos de hardware cargados correctamente')
    return redirect('home')

# Vista para limpiar productos basura
@staff_member_required
def limpiar_productos(request):
    # Eliminar productos de la categoría "Importados" (los de la API)
    try:
        cat_importados = Categoria.objects.get(nombre='Importados')
        count = Producto.objects.filter(categoria=cat_importados).count()
        Producto.objects.filter(categoria=cat_importados).delete()
        cat_importados.delete()
        messages.success(request, f'🗑️ {count} productos importados eliminados')
    except:
        messages.info(request, 'No hay productos importados para eliminar')
    
    return redirect('home')


# ============================================
# NUEVAS VISTAS - MEJORAS BITFORGE
# ============================================

# Vista de Checkout
@login_required
def checkout(request):
    items = CarritoItem.objects.filter(usuario=request.user)
    
    if not items.exists():
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('ver_carrito')
    
    subtotal = sum(item.subtotal() for item in items)
    descuento = Decimal('0')
    cupon = None
    
    # Verificar si hay cupón en sesión
    cupon_codigo = request.session.get('cupon_codigo')
    if cupon_codigo:
        try:
            cupon = Cupon.objects.get(codigo=cupon_codigo)
            if cupon.esta_vigente() and subtotal >= cupon.compra_minima:
                descuento = subtotal * Decimal(cupon.descuento_porcentaje) / 100
                if cupon.descuento_maximo and descuento > cupon.descuento_maximo:
                    descuento = cupon.descuento_maximo
        except Cupon.DoesNotExist:
            del request.session['cupon_codigo']
    
    total = subtotal - descuento
    
    # Obtener perfil del usuario si existe
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        perfil = None
    
    return render(request, 'checkout.html', {
        'items': items,
        'subtotal': subtotal,
        'descuento': descuento,
        'cupon': cupon,
        'total': total,
        'perfil': perfil
    })


# Vista de Procesar Pago (SIMULADO)
@login_required
def procesar_pago(request):
    if request.method != 'POST':
        return redirect('checkout')
    
    items = CarritoItem.objects.filter(usuario=request.user)
    if not items.exists():
        messages.error(request, 'Tu carrito está vacío')
        return redirect('ver_carrito')
    
    # Obtener datos del formulario
    nombre = request.POST.get('nombre_completo', '')
    telefono = request.POST.get('telefono', '')
    direccion = request.POST.get('direccion', '')
    ciudad = request.POST.get('ciudad', '')
    notas = request.POST.get('notas', '')
    
    # Validar campos requeridos
    if not all([nombre, telefono, direccion, ciudad]):
        messages.error(request, 'Por favor completa todos los campos requeridos')
        return redirect('checkout')
    
    # Calcular totales
    subtotal = sum(item.subtotal() for item in items)
    descuento = Decimal('0')
    cupon = None
    
    cupon_codigo = request.session.get('cupon_codigo')
    if cupon_codigo:
        try:
            cupon = Cupon.objects.get(codigo=cupon_codigo)
            if cupon.esta_vigente():
                descuento = subtotal * Decimal(cupon.descuento_porcentaje) / 100
                if cupon.descuento_maximo and descuento > cupon.descuento_maximo:
                    descuento = cupon.descuento_maximo
                cupon.usos_actuales += 1
                cupon.save()
        except Cupon.DoesNotExist:
            pass
    
    total = subtotal - descuento
    
    # Validar stock antes de crear pedido
    for item in items:
        if item.producto.stock < item.cantidad:
            messages.error(request, f'No hay suficiente stock de {item.producto.nombre}')
            return redirect('checkout')
    
    # Crear pedido
    pedido = Pedido.objects.create(
        usuario=request.user,
        total=total,
        nombre_completo=nombre,
        telefono=telefono,
        direccion=direccion,
        ciudad=ciudad,
        notas=notas,
        cupon_aplicado=cupon,
        descuento_aplicado=descuento
    )
    
    # Crear items del pedido y descontar stock
    for item in items:
        PedidoItem.objects.create(
            pedido=pedido,
            producto=item.producto,
            nombre_producto=item.producto.nombre,
            cantidad=item.cantidad,
            precio_unitario=item.producto.precio
        )
        item.producto.stock -= item.cantidad
        item.producto.save()
    
    # Limpiar carrito y cupón de sesión
    items.delete()
    if 'cupon_codigo' in request.session:
        del request.session['cupon_codigo']
    
    messages.success(request, '🎉 ¡Pedido realizado con éxito!')
    return redirect('confirmacion_pedido', pedido_id=pedido.id)


# Vista de Confirmación de Pedido
@login_required
def confirmacion_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'confirmacion_pedido.html', {'pedido': pedido})


# Vista de Mis Pedidos
@login_required
def mis_pedidos(request):
    pedidos = Pedido.objects.filter(usuario=request.user)
    return render(request, 'mis_pedidos.html', {'pedidos': pedidos})


# Vista de Detalle de Pedido
@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario=request.user)
    return render(request, 'detalle_pedido.html', {'pedido': pedido})


# Vista de Aplicar Cupón
@login_required
def aplicar_cupon(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        
        try:
            cupon = Cupon.objects.get(codigo=codigo)
            if cupon.esta_vigente():
                request.session['cupon_codigo'] = codigo
                messages.success(request, f'✅ Cupón aplicado: {cupon.descuento_porcentaje}% de descuento')
            else:
                messages.error(request, '❌ Este cupón ha expirado o ya no está disponible')
        except Cupon.DoesNotExist:
            messages.error(request, '❌ Código de cupón inválido')
    
    return redirect(request.META.get('HTTP_REFERER', 'ver_carrito'))


# Vista de Quitar Cupón
@login_required
def quitar_cupon(request):
    if 'cupon_codigo' in request.session:
        del request.session['cupon_codigo']
        messages.info(request, 'Cupón eliminado')
    return redirect(request.META.get('HTTP_REFERER', 'ver_carrito'))


# Vista de Lista de Deseos
@login_required
def lista_deseos(request):
    deseos = ListaDeseos.objects.filter(usuario=request.user).select_related('producto')
    return render(request, 'lista_deseos.html', {'deseos': deseos})


# Vista de Agregar a Lista de Deseos
@login_required
def agregar_deseos(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    obj, created = ListaDeseos.objects.get_or_create(
        usuario=request.user,
        producto=producto
    )
    
    if created:
        messages.success(request, f'❤️ {producto.nombre} agregado a tu lista de deseos')
    else:
        messages.info(request, 'Este producto ya está en tu lista de deseos')
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# Vista de Eliminar de Lista de Deseos
@login_required
def eliminar_deseos(request, producto_id):
    ListaDeseos.objects.filter(usuario=request.user, producto_id=producto_id).delete()
    messages.success(request, 'Producto eliminado de tu lista de deseos')
    return redirect('lista_deseos')


# Vista de Mover de Deseos a Carrito
@login_required
def mover_deseos_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if producto.stock <= 0:
        messages.error(request, 'Este producto no tiene stock disponible')
        return redirect('lista_deseos')
    
    # Agregar al carrito
    item, created = CarritoItem.objects.get_or_create(
        usuario=request.user,
        producto=producto,
        defaults={'cantidad': 1}
    )
    if not created:
        if item.cantidad < producto.stock:
            item.cantidad += 1
            item.save()
    
    # Eliminar de deseos
    ListaDeseos.objects.filter(usuario=request.user, producto_id=producto_id).delete()
    
    messages.success(request, f'✅ {producto.nombre} movido al carrito')
    return redirect('lista_deseos')


# Vista de Agregar Reseña
@login_required
def agregar_resena(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Verificar si ya reseñó
    if Resena.objects.filter(usuario=request.user, producto=producto).exists():
        messages.warning(request, 'Ya has reseñado este producto')
        return redirect('detalle_producto', producto_id=producto_id)
    
    if request.method == 'POST':
        calificacion = int(request.POST.get('calificacion', 5))
        titulo = request.POST.get('titulo', '')
        comentario = request.POST.get('comentario', '')
        
        if not titulo or not comentario:
            messages.error(request, 'Por favor completa todos los campos')
            return redirect('detalle_producto', producto_id=producto_id)
        
        Resena.objects.create(
            usuario=request.user,
            producto=producto,
            calificacion=calificacion,
            titulo=titulo,
            comentario=comentario
        )
        messages.success(request, '⭐ ¡Gracias por tu reseña!')
    
    return redirect('detalle_producto', producto_id=producto_id)


# Vista de Mi Perfil
@login_required
def mi_perfil(request):
    # Obtener o crear perfil
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    
    # Estadísticas del usuario
    total_pedidos = Pedido.objects.filter(usuario=request.user).count()
    total_resenas = Resena.objects.filter(usuario=request.user).count()
    total_deseos = ListaDeseos.objects.filter(usuario=request.user).count()
    
    if request.method == 'POST':
        # Actualizar perfil
        perfil.telefono = request.POST.get('telefono', '')
        perfil.direccion = request.POST.get('direccion', '')
        perfil.ciudad = request.POST.get('ciudad', '')
        perfil.save()
        
        # Actualizar datos del usuario
        request.user.email = request.POST.get('email', '')
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        messages.success(request, '✅ Perfil actualizado correctamente')
        return redirect('mi_perfil')
    
    return render(request, 'mi_perfil.html', {
        'perfil': perfil,
        'total_pedidos': total_pedidos,
        'total_resenas': total_resenas,
        'total_deseos': total_deseos
    })


# Vista de Suscripción Newsletter
def suscribir_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        
        if not email:
            messages.error(request, 'Por favor ingresa un email válido')
            return redirect('home')
        
        obj, created = SuscripcionNewsletter.objects.get_or_create(
            email=email,
            defaults={'nombre': nombre}
        )
        
        if created:
            messages.success(request, '📧 ¡Te has suscrito al newsletter exitosamente!')
        else:
            messages.info(request, 'Este email ya está suscrito')
    
    return redirect('home')


# Vista de Comparar Productos
@login_required
def comparar_productos(request):
    comparados = ProductoComparado.objects.filter(usuario=request.user).select_related('producto')
    productos = [c.producto for c in comparados]
    
    return render(request, 'comparar.html', {'productos': productos})


# Vista de Agregar a Comparación
@login_required
def agregar_comparar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Máximo 4 productos para comparar
    count = ProductoComparado.objects.filter(usuario=request.user).count()
    if count >= 4:
        messages.warning(request, 'Solo puedes comparar hasta 4 productos')
        return redirect(request.META.get('HTTP_REFERER', 'catalogo'))
    
    obj, created = ProductoComparado.objects.get_or_create(
        usuario=request.user,
        producto=producto
    )
    
    if created:
        messages.success(request, f'📊 {producto.nombre} agregado a comparación')
    else:
        messages.info(request, 'Este producto ya está en la comparación')
    
    return redirect(request.META.get('HTTP_REFERER', 'catalogo'))


# Vista de Eliminar de Comparación
@login_required
def eliminar_comparar(request, producto_id):
    ProductoComparado.objects.filter(usuario=request.user, producto_id=producto_id).delete()
    return redirect('comparar_productos')


# Vista de Limpiar Comparación
@login_required
def limpiar_comparar(request):
    ProductoComparado.objects.filter(usuario=request.user).delete()
    messages.success(request, 'Comparación limpiada')
    return redirect('catalogo')


# Vista de Ofertas
def ofertas(request):
    # Productos con stock bajo (últimas unidades) = oferta
    productos = Producto.objects.filter(disponible=True, stock__gt=0, stock__lte=5)
    return render(request, 'ofertas.html', {'productos': productos})


# Vista de FAQ
def faq(request):
    return render(request, 'faq.html')


# Vista de Contacto
def contacto(request):
    if request.method == 'POST':
        messages.success(request, '✅ Mensaje enviado correctamente. Te responderemos pronto.')
        return redirect('contacto')
    return render(request, 'contacto.html')


# Vista de Sobre Nosotros
def sobre_nosotros(request):
    return render(request, 'sobre_nosotros.html')


# Vista de Búsqueda Avanzada (AJAX)
def busqueda_ajax(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'productos': []})
    
    productos = Producto.objects.filter(
        Q(nombre__icontains=query) | Q(descripcion__icontains=query),
        disponible=True
    )[:5]
    
    data = [{
        'id': p.id,
        'nombre': p.nombre,
        'precio': str(p.precio),
        'imagen': p.imagen_url or ''
    } for p in productos]
    
    return JsonResponse({'productos': data})


# ============================================
# VISTAS ADMIN MEJORADAS
# ============================================

# Vista Admin - Gestionar Pedidos
@staff_member_required
def admin_pedidos(request):
    estado_filtro = request.GET.get('estado', '')
    pedidos = Pedido.objects.all()
    
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)
    
    return render(request, 'admin/gestionar_pedidos.html', {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro
    })


# Vista Admin - Actualizar Estado Pedido
@staff_member_required
def admin_actualizar_pedido(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado:
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Pedido #{pedido.numero_pedido} actualizado a {pedido.get_estado_display()}')
    return redirect('admin_pedidos')


# Vista Admin - Gestionar Cupones
@staff_member_required
def admin_cupones(request):
    cupones = Cupon.objects.all()
    
    if request.method == 'POST':
        # Crear nuevo cupón
        codigo = request.POST.get('codigo', '').upper()
        descripcion = request.POST.get('descripcion', '')
        descuento = int(request.POST.get('descuento', 10))
        fecha_exp = request.POST.get('fecha_expiracion')
        
        if codigo and fecha_exp:
            Cupon.objects.create(
                codigo=codigo,
                descripcion=descripcion,
                descuento_porcentaje=descuento,
                fecha_expiracion=fecha_exp
            )
            messages.success(request, f'✅ Cupón {codigo} creado correctamente')
    
    return render(request, 'admin/gestionar_cupones.html', {'cupones': cupones})


# Vista Admin - Toggle Cupón Activo
@staff_member_required
def admin_toggle_cupon(request, cupon_id):
    cupon = get_object_or_404(Cupon, id=cupon_id)
    cupon.activo = not cupon.activo
    cupon.save()
    estado = "activado" if cupon.activo else "desactivado"
    messages.success(request, f'Cupón {cupon.codigo} {estado}')
    return redirect('admin_cupones')


# Vista Admin - Dashboard Mejorado
@staff_member_required  
def panel_admin_mejorado(request):
    from django.db.models import Sum
    from datetime import timedelta
    
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    
    # Estadísticas generales
    total_productos = Producto.objects.count()
    productos_agotados = Producto.objects.filter(stock=0).count()
    productos_bajo_stock = Producto.objects.filter(stock__gt=0, stock__lte=3).count()
    solicitudes_pendientes = Solicitud.objects.filter(estado='pendiente').count()
    
    # Estadísticas de pedidos
    total_pedidos = Pedido.objects.count()
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_hoy = Pedido.objects.filter(fecha_pedido__date=hoy).count()
    
    # Ventas
    ventas_totales = Pedido.objects.aggregate(total=Sum('total'))['total'] or 0
    ventas_mes = Pedido.objects.filter(fecha_pedido__date__gte=hace_30_dias).aggregate(total=Sum('total'))['total'] or 0
    
    # Últimos pedidos
    ultimos_pedidos = Pedido.objects.all()[:5]
    
    # Productos más vendidos
    productos_vendidos = PedidoItem.objects.values('nombre_producto').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:5]
    
    # Suscriptores newsletter
    suscriptores = SuscripcionNewsletter.objects.filter(activo=True).count()
    
    return render(request, 'admin/panel_admin.html', {
        'total_productos': total_productos,
        'productos_agotados': productos_agotados,
        'productos_bajo_stock': productos_bajo_stock,
        'solicitudes_pendientes': solicitudes_pendientes,
        'total_pedidos': total_pedidos,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_hoy': pedidos_hoy,
        'ventas_totales': ventas_totales,
        'ventas_mes': ventas_mes,
        'ultimos_pedidos': ultimos_pedidos,
        'productos_vendidos': productos_vendidos,
        'suscriptores': suscriptores
    })


# ============== NUEVAS VISTAS UI ENHANCEMENT ==============

# Vista AJAX para búsqueda en vivo
def busqueda_ajax(request):
    query = request.GET.get('q', '')
    productos = []
    
    if query and len(query) >= 2:
        resultado = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query),
            disponible=True
        )[:10]
        
        productos = [{
            'id': p.id,
            'nombre': p.nombre,
            'precio': str(p.precio),
            'imagen': p.imagen_url or ''
        } for p in resultado]
    
    return JsonResponse({'productos': productos})


# Vista de detalle de producto mejorada
def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Productos relacionados (misma categoría)
    relacionados = Producto.objects.filter(
        categoria=producto.categoria,
        disponible=True
    ).exclude(id=producto.id)[:4]
    
    # Reseñas del producto
    resenas = Resena.objects.filter(producto=producto).order_by('-fecha')
    
    return render(request, 'detalle_producto.html', {
        'producto': producto,
        'relacionados': relacionados,
        'resenas': resenas
    })


# Página de ofertas (productos con bajo stock)
def ofertas(request):
    productos = Producto.objects.filter(
        disponible=True,
        stock__gt=0,
        stock__lte=5
    ).order_by('stock')[:12]
    
    return render(request, 'ofertas.html', {'productos': productos})


# Página de preguntas frecuentes
def faq(request):
    return render(request, 'faq.html')


# Página de contacto
def contacto(request):
    if request.method == 'POST':
        # Simulamos el envío del formulario
        messages.success(request, '✅ ¡Mensaje enviado! Te responderemos pronto.')
        return redirect('contacto')
    return render(request, 'contacto.html')


# Página sobre nosotros
def sobre_nosotros(request):
    return render(request, 'sobre_nosotros.html')


# Vista de gestión de clientes (Admin)
@staff_member_required
def admin_clientes(request):
    from django.contrib.auth.models import User
    from django.db.models import Sum, Count
    from datetime import timedelta
    
    # Obtener todos los usuarios que no son staff
    clientes = User.objects.filter(is_staff=False).annotate(
        total_pedidos=Count('pedido'),
        total_gastado=Sum('pedido__total')
    ).order_by('-date_joined')
    
    # Estadísticas
    total_clientes = clientes.count()
    clientes_activos = User.objects.filter(is_staff=False, pedido__isnull=False).distinct().count()
    
    hace_30_dias = timezone.now() - timedelta(days=30)
    nuevos_mes = User.objects.filter(is_staff=False, date_joined__gte=hace_30_dias).count()
    
    suscriptores = SuscripcionNewsletter.objects.filter(activo=True).count()
    
    return render(request, 'admin/gestionar_clientes.html', {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'nuevos_mes': nuevos_mes,
        'suscriptores': suscriptores
    })


# Vista de exportación de reportes (Admin)
@staff_member_required
def admin_exportar_reporte(request):
    import csv
    from django.http import HttpResponse
    
    tipo = request.GET.get('tipo', 'pedidos')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reporte_{tipo}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    if tipo == 'pedidos':
        writer.writerow(['Número', 'Cliente', 'Total', 'Estado', 'Fecha'])
        for pedido in Pedido.objects.all().order_by('-fecha_pedido'):
            writer.writerow([
                pedido.numero_pedido,
                pedido.usuario.username,
                pedido.total,
                pedido.get_estado_display(),
                pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')
            ])
    elif tipo == 'productos':
        writer.writerow(['Nombre', 'Precio', 'Stock', 'Categoría', 'Disponible'])
        for producto in Producto.objects.all():
            writer.writerow([
                producto.nombre,
                producto.precio,
                producto.stock,
                producto.categoria.nombre if producto.categoria else 'N/A',
                'Sí' if producto.disponible else 'No'
            ])
    elif tipo == 'clientes':
        from django.contrib.auth.models import User
        writer.writerow(['Username', 'Email', 'Fecha Registro', 'Total Pedidos'])
        for user in User.objects.filter(is_staff=False):
            writer.writerow([
                user.username,
                user.email,
                user.date_joined.strftime('%d/%m/%Y'),
                Pedido.objects.filter(usuario=user).count()
            ])
    
    return response


