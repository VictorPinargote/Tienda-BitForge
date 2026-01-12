from django.shortcuts import render

# Vista principal - Página de inicio
def home(request):
    #Muestra la página principal con el catálogo de productos.
    return render(request, 'index.html') #renderiza el template y lo devuelve en la página web



# Create your views here.
