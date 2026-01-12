from django.db import models
from django.contrib.auth.models import User 

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
    email = models.EmailField(unique=True) #unique=True permite que el campo sea único y usar emailfield para validar que sea un email
    telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Proveedores"

#Modelo de Producto
class Producto(models.Model):
    #tipos de productos
    TIPO_CHOICES = (
        ('componente', 'Componente'),
        ('kit', 'Kit'),
        ('pc_armada', 'PC Armada'),
    )
    #atributos
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveBigIntegerField(default=0) #positivebigintegerfield permite que el campo sea un numero entero positivo
    imagen_url = models.URLField(blank=True, null=True) #urlfield permite que el campo sea una url
    #relacion con la categoria 
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    #on_delete=models.CASCADE significa que si se elimina la categoria, se eliminan todos los productos
    
    #relacion con el proveedor
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True)
    #on_delete=models.SET_NULL, null=True significa que si se elimina el proveedor, se establece el campo a null
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='componente') #con el choices hace que use la tupla TIPO_CHOICES
    disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True) #auto_now_add=True crea un campo que almacena la fecha y hora de creacion del objeto

    def __str__(self):
        return f"{self.nombre} - {self.precio}"

    def get_estado_stock(self):
        # para que se muestre el estado al cliente
        if self.stock == 0:
            return "Agotado"
        elif self.stock <= 3:
            return "ultimas unidades"
        else:
            return "Disponible"

#modelo de solicitud
class Solicitud(models.Model):
    #Estados de la solicitud
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
    ]
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    nota_cliente = models.TextField(blank=True)
    
    def __str__(self):
        return f"Solicitud #{self.id} - {self.producto.nombre}"
    class Meta:
        verbose_name_plural = "Solicitudes"
        ordering = ['-fecha_solicitud']

#Modelo de carrito
class CarritoItem(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'producto')  # Un usuario no puede tener el mismo producto dos veces
        verbose_name_plural = "Items del Carrito"
    
    def __str__(self):
        return f"{self.usuario.username} - {self.producto.nombre} x{self.cantidad}"
    
    def subtotal(self):
        return self.producto.precio * self.cantidad
    