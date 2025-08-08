from . import views
from django.urls import path

app_name = 'inventory'

urlpatterns = [
    #Product
    path('',views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('<int:product_id>/edit/', views.product_update, name='product_update'),
    #path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('<int:product_id>/update_stock/', views.update_stock, name='update_stock'),

]
