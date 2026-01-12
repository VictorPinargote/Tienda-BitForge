from django.urls import path
from . import views

urlpatterns = [
    #home
    path('', views.home, name='home'),

    #registro
    path('registro/', views.registro, name='registro'),
]