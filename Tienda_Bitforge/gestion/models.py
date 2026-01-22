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


# ============================================
# NUEVOS MODELOS - MEJORAS BITFORGE
# ============================================

# Modelo de Pedido (Order)
class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    numero_pedido = models.CharField(max_length=20, unique=True, editable=False)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Información de envío
    nombre_completo = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=50)
    notas = models.TextField(blank=True)
    
    # Fechas
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Cupón aplicado (opcional)
    cupon_aplicado = models.ForeignKey('Cupon', on_delete=models.SET_NULL, null=True, blank=True)
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-fecha_pedido']
        verbose_name_plural = "Pedidos"
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            import random
            import string
            self.numero_pedido = 'BF' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.usuario.username}"


# Modelo de Items del Pedido
class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    nombre_producto = models.CharField(max_length=100)  # Guardamos el nombre por si se elimina el producto
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    def subtotal(self):
        return self.precio_unitario * self.cantidad
    
    def __str__(self):
        return f"{self.nombre_producto} x{self.cantidad}"


# Modelo de Reseña (Review)
class Resena(models.Model):
    CALIFICACION_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1 a 5 estrellas
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='resenas')
    calificacion = models.IntegerField(choices=CALIFICACION_CHOICES)
    titulo = models.CharField(max_length=100)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'producto')  # Un usuario solo puede reseñar un producto una vez
        ordering = ['-fecha']
        verbose_name_plural = "Reseñas"
    
    def __str__(self):
        return f"Reseña de {self.usuario.username} - {self.producto.nombre}"


# Modelo de Lista de Deseos (Wishlist)
class ListaDeseos(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'producto')
        verbose_name_plural = "Listas de Deseos"
    
    def __str__(self):
        return f"{self.usuario.username} - {self.producto.nombre}"


# Modelo de Cupón de Descuento
from django.core.validators import MinValueValidator, MaxValueValidator

class Cupon(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=100)
    descuento_porcentaje = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )  # Porcentaje de descuento (1-100)
    descuento_maximo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Tope máximo
    compra_minima = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Compra mínima requerida
    activo = models.BooleanField(default=True)
    fecha_expiracion = models.DateField()
    usos_maximos = models.PositiveIntegerField(default=100)
    usos_actuales = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Cupones"
    
    def esta_vigente(self):
        from django.utils import timezone
        hoy = timezone.now().date()
        return self.activo and self.fecha_expiracion >= hoy and self.usos_actuales < self.usos_maximos
    
    def __str__(self):
        return f"{self.codigo} - {self.descuento_porcentaje}%"


# Modelo de Perfil de Usuario Extendido
class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('cliente', 'Cliente'),
        ('bodeguero', 'Bodeguero'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrador'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=50, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username} ({self.get_rol_display()})"
    
    def es_cliente(self):
        return self.rol == 'cliente'
    
    def es_bodeguero(self):
        return self.rol == 'bodeguero'
    
    def es_supervisor(self):
        return self.rol == 'supervisor'
    
    def es_admin(self):
        return self.rol == 'admin'
    
    def puede_ver_pedidos(self):
        return self.rol in ['supervisor', 'admin'] or self.usuario.is_superuser
    
    def puede_ver_productos(self):
        return self.rol in ['bodeguero', 'admin'] or self.usuario.is_superuser
    
    def puede_gestionar_usuarios(self):
        return self.rol in ['supervisor', 'admin'] or self.usuario.is_superuser
    
    def puede_ver_cupones(self):
        return self.rol in ['supervisor', 'admin'] or self.usuario.is_superuser
    
    def puede_ver_graficas(self):
        return self.rol in ['supervisor', 'admin'] or self.usuario.is_superuser
    
    class Meta:
        verbose_name_plural = "Perfiles de Usuario"


# Modelo de Suscripción Newsletter
class SuscripcionNewsletter(models.Model):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=50, blank=True)
    fecha_suscripcion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Suscripciones Newsletter"
    
    def __str__(self):
        return self.email


# Modelo para Productos Comparados (sesión temporal)
class ProductoComparado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('usuario', 'producto')
        verbose_name_plural = "Productos Comparados"
    
    def __str__(self):
        return f"{self.usuario.username} compara {self.producto.nombre}"


# Modelo de Devolución
class Devolucion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
    ]
    
    MOTIVO_CHOICES = [
        ('defectuoso', 'Producto Defectuoso'),
        ('incorrecto', 'Producto Incorrecto'),
        ('danado', 'Producto Dañado'),
        ('no_satisface', 'No Satisface Expectativas'),
        ('otro', 'Otro'),
    ]
    
    pedido = models.ForeignKey('Pedido', on_delete=models.CASCADE, related_name='devoluciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    descripcion = models.TextField(help_text="Describe el problema")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Admin response
    respuesta_admin = models.TextField(blank=True, null=True)
    monto_reembolso = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name_plural = "Devoluciones"
    
    def __str__(self):
        return f"Devolución #{self.id} - Pedido #{self.pedido.numero_pedido}"
