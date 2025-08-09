from . import views
from django.urls import path

app_name = "users"

urlpatterns = [
    path('',views.login_view, name="login"),
    path('logout',views.log_out, name="logout"),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),


    #Products
    path('products/',views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('<int:product_id>/edit/', views.product_update, name='product_update'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('<int:product_id>/update_stock/', views.update_stock, name='update_stock'),

    #Category
    path('category/',views.category_list, name='category_list'),
    path('category/add/', views.category_add, name='category_add'),
    path('category/<int:category_id>/edit/', views.category_update, name='category_update'),
    path('category/<int:category_id>/delete/', views.category_delete, name='category_delete'),

    #Supplier
    path('supplier/',views.supplier_list, name='supplier_list'),
    path('supplier/add/', views.supplier_add, name='supplier_add'),
    path('supplier/<int:supplier_id>/edit/', views.supplier_update, name='supplier_update'),
    path('supplier/<int:supplier_id>/delete/', views.supplier_delete, name='supplier_delete'),

    #Reports
    path('reports/inventory/', views.inventory_report , name='inventory_report'),
    path('reports/suppliers/', views.supplier_report , name='supplier_report'),
]
