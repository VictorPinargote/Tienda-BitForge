from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm #Formulario para creación de usuario
from django.contrib import messages #Mensajes de confirmación
from .models import Producto, CarritoItem, Solicitud
from django.contrib.admin.views.decorators import staff_member_required

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

    

# Create your views here.
