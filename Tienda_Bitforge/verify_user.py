import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BitForge.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = 'joelp'
password = 'admin1470'

print(f"--- Creando/Verificando usuario: {username} ---")

try:
    u = User.objects.get(username=username)
    print(f"Usuario existe (ID: {u.id})")
    u.set_password(password)
    u.is_staff = True
    u.is_superuser = True
    u.is_active = True
    u.save()
    print("Contraseña y permisos actualizados")
except User.DoesNotExist:
    u = User.objects.create_superuser(username, 'joelp@bitforge.com', password)
    print("Usuario superadmin creado exitosamente")

print(f"Usuario: {username}")
print(f"Password: {password}")
print(f"Staff: {u.is_staff}, Super: {u.is_superuser}, Active: {u.is_active}")
print("--- Listo para login ---")
