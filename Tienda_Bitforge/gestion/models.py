from django.db import models

# Create your models here.

#Modelo de Categoria
class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True) #blank=True y null=True permiten que el campo sea opcional y nulo
    icono = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Categorias" #Nombre en singular en la admin

#Modelo de Proveedor
class Proveedor(models.Model):
    nombre = models.CharField(max_length=50)
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Proveedores"