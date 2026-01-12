from django.urls import path
from . import views

urlpatterns = [
    #home
    path('', views.home, name='home'),

    #registro
    path('registro/', views.registro, name='registro'),

    # Carrito
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),

    # Solicitudes
    path('solicitud/crear/<int:producto_id>/', views.crear_solicitud, name='crear_solicitud'),
    path('mis-solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),

    # Admin/Staff
    path('admin/solicitudes/', views.ver_solicitudes_admin, name='solicitudes_admin'),
    path('admin/solicitud/completar/<int:solicitud_id>/', views.marcar_completada, name='marcar_completada'),

    # API y Catálogo
    path('importar-precios/', views.importar_precios, name='importar_precios'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('catalogo/', views.catalogo, name='catalogo'),

    # Bodega/Stock
    path('admin/stock/', views.gestion_stock, name='gestion_stock'),
    path('admin/stock/actualizar/<int:producto_id>/', views.actualizar_stock, name='actualizar_stock'),
]