from django.shortcuts import render
from .models import Producto

# Vista principal - Página de inicio
def home(request):
    #Muestra la página principal con el catálogo de productos.
    productos = Producto.objects.filter(disponible=True)
    return render(request, 'index.html', {'productos': productos}) #renderiza el template y lo devuelve en la página web

# Create your views here.
