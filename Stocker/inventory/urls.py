from . import views
from django.urls import path

urlpatterns = [
    #Product
    path('products/',views.product_list, name='product_list'),
    
]
