from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm #Formulario para creación de usuario
from django.contrib import messages #Mensajes de confirmación
from .models import Producto

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

# Create your views here.
