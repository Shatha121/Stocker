from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from inventory.models import Product, Category, Supplier


# Create your views here.

def is_admin(user):
    return user.is_staff or user.is_superuser

def login_view(request:HttpResponse):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")
        user = authenticate(request, username=identifier, password=password)

        if user == None:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            auth_login(request,user)
            if user.is_superuser:
                return redirect("users:admin_dashboard")
            elif user.groups.filter(name='Employee').exists():
                return redirect("inventory:product_list")
            else:
                return redirect(request.GET.get("next","/"))
        else:
            messages.error(request,"There is no user with these information", "alert-danger")

    return render(request, "users/login.html", {})

def log_out(request:HttpRequest):
    logout(request)
    return redirect("users:login")

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request:HttpRequest):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    low_stock_items = Product.objects.filter(quantity_in_stock__lte=5)
    total_low_stock = low_stock_items.count()

    context = {
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "total_categories": total_categories,
        "low_stock_items": low_stock_items,
        "total_low_stock": total_low_stock,
    }

    return render(request, "users/admin_dashboard.html", context)