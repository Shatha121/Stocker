from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib import messages
from inventory.models import Product, Category, Supplier, StockUpdate
from inventory.forms import ProductForm, SupplierForm, CategoryForm
from django.core.paginator import Paginator
from django.db.models import Q, F ,Count, Sum
from django.utils.timezone import now, timedelta
from django.core.mail import send_mail
import csv
from stocker import settings
from .forms import ProductImportForm
import json

# Create your views here.

def is_admin(user):
    return user.is_staff or user.is_superuser

def sign_up_view(request:HttpRequest):
    if request.method == "POST":
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username = request.POST.get('identifier')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('users:signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken")
            return redirect('users:signup')
        
        user = User.objects.create_user(username=username, password=password, email=email, first_name=firstname, last_name=lastname)

        try:
            employee_group = Group.objects.get(name="Employee")
            user.groups.add(employee_group)
        except:
            messages.error(request,"Employee group doesn't exist.")
            return redirect("users:signup")
        messages.success(request, "Account created successfully. you can now log in")
        return render(request, 'users/login.html')
    return render(request, 'users/signup.html')

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
            if user.groups.filter(name='Employee').exists():
                return redirect("inventory:product_list")
            elif user.groups.filter(name='Admin').exists():
                return redirect("users:admin_dashboard")
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

    category_data = Category.objects.annotate(product_count = Count('product'))
    labels = json.dumps([cat.name for cat in category_data])
    data = json.dumps([cat.product_count for cat in category_data])

    supplier_data = Supplier.objects.annotate(product_count = Count('product'))
    supplier_labels = json.dumps([sup.name for sup in supplier_data])
    supplier_data_values = json.dumps([sup.product_count for sup in supplier_data])

    context = {
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "total_categories": total_categories,
        "low_stock_items": low_stock_items,
        "total_low_stock": total_low_stock,
        'labels': labels,
        "data": data,
        'supplier_labels': supplier_labels,
        "supplier_data_values": supplier_data_values,
    }

    return render(request, "users/admin_dashboard.html", context)


@login_required
@permission_required('inventory.change_product', raise_exception=True)
def update_stock(request:HttpRequest, product_id:int):
    product = Product.objects.get(pk = product_id)
    if request.method == 'POST':
        try:
            quantity_change = int(request.POST.get('quantity_change'))
        except:
            messages.error(request,"Invaild quantity.")
            return redirect('users:update_stock', product_id=product.id)
        
        old_quantity = product.quantity_in_stock
        product.quantity_in_stock += quantity_change


        if product.quantity_in_stock < 0 :
            messages.error(request, "Resulting stock can't be negative.")
            return redirect('users:update_stock', product_id=product.id)
        
        product.save()
        
        StockUpdate.objects.create(
            product=product,
            updated_by = request.user,
            quantity_change = quantity_change,
            note=request.POST.get('note','')
        )
        
        if product.quantity_in_stock <= 5 and old_quantity > 5:
            send_mail(
                subject = f"Low Stock Alert: {product.name}",
                message = f"{product.name} has only {product.quantity_in_stock} left in stock.",
                from_email= settings.EMAIL_HOST_USER,
                recipient_list = [settings.EMAIL_HOST_USER],
                fail_silently = False,
            )


        messages.success(request, "Stock updated successfully.")
        return redirect('users:product_list')
    return render(request, 'users/update_stock.html', {'product':product})



#Product
@login_required
def product_list(request:HttpRequest):
    query = request.GET.get('q')
    products = Product.objects.all()
    category = request.GET.get('category')
    supplier = request.GET.get('supplier')
    if query:
        products = products.filter(name__icontains=query)
    if category:
        products = products.filter(category__id=category)
    if supplier:
        products = products.filter(suppliers__id=supplier)
    paginator = Paginator(products, 10)
    page = request.GET.get('page')
    products =  paginator.get_page(page)
    context = {
        "products": products,
        "categories": Category.objects.all(),
        "suppliers": Supplier.objects.all(),
    }
    return render(request, 'users/product_list.html', context)


@login_required
@permission_required('inventory.add_product', raise_exception=True)
def product_add(request:HttpRequest):
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            if int(request.POST.get('quantity_in_stock')) <= 5:
                messages.error(request, "Stock must be greater than 5 when adding or updating a product.")
                return redirect('users:product_add')
            form.save()
            messages.success(request, "Product added successfully")
            return redirect('users:product_list')
    else:
        form = ProductForm()
    return render(request, 'users/add_product.html', {'form':form , 'categories':categories, 'suppliers':suppliers})


@login_required
def product_detail(request, product_id:int):
    product = Product.objects.get(pk = product_id)
    return render(request, 'users/detail_product.html', {'product':product})


@login_required
@permission_required('inventory.change_product', raise_exception=True)
def product_update(request:HttpRequest, product_id:int):
    product = Product.objects.get(pk = product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.category_id = request.POST.get('category')
        product.quantity_in_stock = request.POST.get('quantity_in_stock')
        product.expiry_date = request.POST.get('expiry_date') or None

        if 'image' in request.FILES:
            product.image = request.FILES['image'] 
        
        if int(request.POST.get('quantity_in_stock')) <= 5:
                messages.error(request, "Stock must be greater than 5 when adding or updating a product.")
                return redirect('users:product_update', product_id = product.id)

        product.save()
        product.suppliers.set(request.POST.getlist('suppliers'))

        messages.success(request, "Product updated successfully.")
        return redirect('users:product_list')
    
    context = {
        'product': product,
        'category_choices': [(c.id, c.name) for c in Category.objects.all()],
        'suppliers': Supplier.objects.all(),
    }

    return render(request, 'users/update_product.html', context)

@login_required
@permission_required('inventory.delete_product', raise_exception=True)
def product_delete(request:HttpRequest, product_id:int):
    product = Product.objects.get(pk = product_id)
    product.delete()
    messages.success(request, "Product deleted successfully")
    return redirect('users:product_list')



#Category
@login_required
def category_list(request:HttpRequest):
    query = request.GET.get('q')
    categories = Category.objects.all()
    if query:
        categories = categories.filter(name__icontains=query)
    paginator = Paginator(categories, 10)
    page = request.GET.get('page')
    categories =  paginator.get_page(page)
    return render(request, 'users/manage_category.html', {'categories':categories})


@login_required
@permission_required('inventory.add_category', raise_exception=True)
def category_add(request:HttpRequest):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully")
            return redirect('users:category_list')
    else:
        form = CategoryForm()
    return render(request, 'users/add_category.html', {'form':form})




@login_required
@permission_required('inventory.change_category', raise_exception=True)
def category_update(request:HttpRequest, category_id:int):
    category = Category.objects.get(pk=category_id)
    form = CategoryForm(request.POST, instance=category)
    if form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect('users:category_list')
    return render(request, 'users/category_form.html', {'form':form})

@login_required
@permission_required('inventory.delete_category', raise_exception=True)
def category_delete(request:HttpRequest, category_id:int):
    category = Category.objects.get(pk = category_id)
    category.delete()
    messages.success(request, "Category deleted successfully")
    return redirect('users:category_list')





#Supplier
@login_required
def supplier_list(request:HttpRequest):
    query = request.GET.get('q')
    suppliers = Supplier.objects.all()
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query)
        ).distinct()
    paginator = Paginator(suppliers, 10)
    page = request.GET.get('page')
    suppliers =  paginator.get_page(page)
    return render(request, 'users/manage_supplier.html', {'suppliers':suppliers})


@login_required
@permission_required('inventory.add_supplier', raise_exception=True)
def supplier_add(request:HttpRequest):
    if request.method == "POST":
        form = SupplierForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added successfully")
            return redirect('users:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'users/add_supplier.html', {'form':form})




@login_required
@permission_required('inventory.change_supplier', raise_exception=True)
def supplier_update(request:HttpRequest, supplier_id:int):
    supplier = Supplier.objects.get(pk=supplier_id)
    if request.method == "POST":
        form = SupplierForm(request.POST, request.FILES, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier updated successfully")
            return redirect('users:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'users/update_supplier.html', {'form':form, 'supplier':supplier})

@login_required
@permission_required('inventory.delete_supplier', raise_exception=True)
def supplier_delete(request:HttpRequest, supplier_id:int):
    supplier = Supplier.objects.get(pk = supplier_id)
    supplier.delete()
    messages.success(request, "Supplier deleted successfully")
    return redirect('users:supplier_list')


@login_required
@user_passes_test(is_admin)
def inventory_report(request:HttpRequest):
    products = Product.objects.all()
    total_products = products.count()
    total_stock = products.aggregate(total=Sum('quantity_in_stock'))['total'] or 0
    low_stock_products = products.filter(quantity_in_stock__lte=5)

    soon = now().date() + timedelta(days=30)

    expiring_products = products.filter(expiry_date__lte=soon, expiry_date__isnull=False)

    context = {
        'total_products':total_products,
        'total_stock':total_stock,
        'low_stock_products':low_stock_products,
        'expiring_products':expiring_products,
    }
    return render(request, 'reports/inventory_report.html', context)


@login_required
@user_passes_test(is_admin)
def supplier_report(request:HttpRequest):
    suppliers = Supplier.objects.annotate(
        product_count = Count('product'),
        total_stock= Sum('product__quantity_in_stock')
    )

    context = {
        'suppliers': suppliers,
    }
    return render(request, 'reports/supplier_report.html', context)


@login_required
@user_passes_test(is_admin)
def inventory_report_csv(request:HttpRequest):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Product Name', 'Category', 'Suppliers' ,'Quantity In Stock', 'Expiry Date'])

    products = Product.objects.all()
    for p in products:
        supplier_names = ", ".join([s.name for s in p.suppliers.all()])
        product_image_url = request.build_absolute_uri(p.image.url) if p.image else ''
        writer.writerow([p.name, p.category.name, supplier_names , p.quantity_in_stock, p.expiry_date or 'N/A', product_image_url])
    return response

@login_required
@user_passes_test(is_admin)
def supplier_report_csv(request:HttpRequest):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplier_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Supplier Name', 'Email', 'Phone', 'Products Supplied' ,'Total Stock', 'Logo URL'])

    suppliers = Supplier.objects.annotate(
        product_count = Count('product'),
        total_stock = Sum('product__quantity_in_stock')
    )
    for s in suppliers:
        logo_url = request.build_absolute_uri(s.logo.url) if s.logo else ''
        writer.writerow([s.name, s.email or '', s.phone or '', s.product_count or 0, s.total_stock or 0, logo_url])
    return response