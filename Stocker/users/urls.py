from . import views
from django.urls import path

app_name = "users"

urlpatterns = [
    path('',views.login_view, name="login"),
    path('logout',views.log_out, name="logout"),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard')
]
