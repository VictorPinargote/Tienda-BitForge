from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Registro
    path('registro/', views.registro, name='registro'),

    # Carrito
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('carrito/actualizar/<int:item_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    
    # Checkout y Pagos (SIMULADO)
    path('checkout/', views.checkout, name='checkout'),
    path('procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('pedido/confirmacion/<int:pedido_id>/', views.confirmacion_pedido, name='confirmacion_pedido'),
    
    # Pedidos
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    
    # Cupones
    path('aplicar-cupon/', views.aplicar_cupon, name='aplicar_cupon'),
    path('quitar-cupon/', views.quitar_cupon, name='quitar_cupon'),
    
    # Lista de Deseos
    path('deseos/', views.lista_deseos, name='lista_deseos'),
    path('deseos/agregar/<int:producto_id>/', views.agregar_deseos, name='agregar_deseos'),
    path('deseos/eliminar/<int:producto_id>/', views.eliminar_deseos, name='eliminar_deseos'),
    path('deseos/mover-carrito/<int:producto_id>/', views.mover_deseos_carrito, name='mover_deseos_carrito'),
    
    # Reseñas
    path('resena/agregar/<int:producto_id>/', views.agregar_resena, name='agregar_resena'),
    
    # Perfil
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    
    # Newsletter
    path('newsletter/', views.suscribir_newsletter, name='suscribir_newsletter'),
    
    # Comparador
    path('comparar/', views.comparar_productos, name='comparar_productos'),
    path('comparar/agregar/<int:producto_id>/', views.agregar_comparar, name='agregar_comparar'),
    path('comparar/eliminar/<int:producto_id>/', views.eliminar_comparar, name='eliminar_comparar'),
    path('comparar/limpiar/', views.limpiar_comparar, name='limpiar_comparar'),
    
    # Páginas Estáticas
    path('ofertas/', views.ofertas, name='ofertas'),
    path('faq/', views.faq, name='faq'),
    path('contacto/', views.contacto, name='contacto'),
    path('sobre-nosotros/', views.sobre_nosotros, name='sobre_nosotros'),
    
    # Búsqueda AJAX
    path('busqueda/', views.busqueda_ajax, name='busqueda_ajax'),

    # Solicitudes Cliente (existente y nueva)
    path('solicitud/generica/', views.crear_solicitud_generica, name='crear_solicitud_generica'),
    path('solicitud/crear/<int:producto_id>/', views.crear_solicitud, name='crear_solicitud'),
    path('mis-solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),

    # API y Catálogo (existente)
    path('importar-precios/', views.importar_precios, name='importar_precios'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('catalogo/', views.catalogo, name='catalogo'),

    # Admin/Staff (USANDO staff/ EN VEZ DE admin/ PARA EVITAR CONFLICTO)
    path('staff/solicitudes/', views.ver_solicitudes_admin, name='solicitudes_admin'),
    path('staff/solicitud/completar/<int:solicitud_id>/', views.marcar_completada, name='marcar_completada'),
    path('staff/panel/', views.panel_admin_mejorado, name='panel_admin'),
    path('staff/pedidos/', views.admin_pedidos, name='admin_pedidos'),
    path('staff/pedido/actualizar/<int:pedido_id>/', views.admin_actualizar_pedido, name='admin_actualizar_pedido'),
    path('staff/cupones/', views.admin_cupones, name='admin_cupones'),
    path('staff/cupon/toggle/<int:cupon_id>/', views.admin_toggle_cupon, name='admin_toggle_cupon'),

    # Bodega/Stock
    path('staff/stock/', views.gestion_stock, name='gestion_stock'),
    path('staff/stock/actualizar/<int:producto_id>/', views.actualizar_stock, name='actualizar_stock'),
    
    # Utilidades Admin
    path('staff/cargar-productos/', views.cargar_productos_demo, name='cargar_productos'),
    path('staff/limpiar-productos/', views.limpiar_productos, name='limpiar_productos'),
    path('staff/importar-pcpartpicker/', views.importar_pcpartpicker, name='importar_pcpartpicker'),
    
    # Búsqueda PCPartPicker (AJAX)
    path('buscar-pcpartpicker/', views.buscar_pcpartpicker, name='buscar_pcpartpicker'),
    
    # Nuevas funcionalidades Admin
    path('staff/clientes/', views.admin_clientes, name='admin_clientes'),
    path('staff/exportar/', views.admin_exportar_reporte, name='admin_exportar'),
    
    # Devoluciones (Cliente)
    path('devolucion/solicitar/<int:pedido_id>/', views.solicitar_devolucion, name='solicitar_devolucion'),
    path('mis-devoluciones/', views.mis_devoluciones, name='mis_devoluciones'),
    
    # Devoluciones (Admin)
    path('staff/devoluciones/', views.admin_devoluciones, name='admin_devoluciones'),
    path('staff/devolucion/<int:devolucion_id>/', views.gestionar_devolucion, name='gestionar_devolucion'),
]
