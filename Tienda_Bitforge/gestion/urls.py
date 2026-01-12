from django.urls import path
from . import views

urlpatterns = [
#URLS PRINCIPAL
    path('', views.home, name='home'), 
]