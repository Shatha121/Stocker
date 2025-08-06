from django.shortcuts import render , redirect
from django.http import HttpRequest, HttpResponse
from .models import Product, Category, Supplier
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .forms import ProductForm, CategoryForm, SupplierForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test


# Create your views here.

def is_employee(user):
    return user.groups.filter(name='Employee').exists()


@login_required
@user_passes_test(lambda u: u.has_perm('inventory.change_stock'))
def update_stock(request:HttpRequest, stock_id:int):
    product = Product.objects.get(pk = stock_id)
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        if quantity and quantity.isdigit():
            product.quantity_in_stock = int(quantity)
            product.save()
            messages.success(request, "Stock updated successfully.")
            return redirect('product_list')
        else:
            messages.error(request, "Invalid quantity entered.")
        return render(request, 'inventory/update_stock.html', {'product':product})



#Product
@login_required
def product_list(request:HttpRequest):
    query = request.GET.get('q')
    products = Product.objects.all()
    if query:
        product = products.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query) | Q(suppliers__name__icontains=query)
        ).distinct()
    paginator = Paginator(product, 10)
    page = request.GET.get('page')
    products =  paginator.GET.get_page(page)
    return render(request, 'inventory/product_list.html', {'products':products})


@login_required
@permission_required('inventory.add_product', raise_exception=True)
def product_create(request:HttpRequest):
    form = ProductForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Product added successfully.")
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {'form':form})


@login_required
def product_detail(request, product_id:int):
    product = Product.objects.get(pk = product_id)
    return render(request, 'inventory/product_detail.html', {'product':product})


@login_required
@permission_required('inventory.change_product', raise_exception=True)
def product_update(request:HttpRequest):
    form = ProductForm(request.POST, instance=Product)
    if form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {'form':form})

@login_required
@permission_required('inventory.delete_product', raise_exception=True)
def product_delete(request:HttpRequest, product_id:int):
    product = Product.objects.get(pk = product_id)
    product.delete()
    messages.success(request, "Product deleted successfully")
    return redirect('product_list')



#Category
@login_required
def category_list(request:HttpRequest):
    query = request.GET.get('q')
    categories = Category.objects.all()
    if query:
        category = categories.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query) | Q(suppliers__name__icontains=query)
        ).distinct()
    paginator = Paginator(category, 10)
    page = request.GET.get('page')
    categories =  paginator.GET.get_page(page)
    return render(request, 'inventory/category_list.html', {'categories':categories})


@login_required
@permission_required('inventory.add_category', raise_exception=True)
def category_create(request:HttpRequest):
    form = CategoryForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Category added successfully.")
        return redirect('category_list')
    return render(request, 'inventory/category_form.html', {'form':form})




@login_required
@permission_required('inventory.change_category', raise_exception=True)
def category_update(request:HttpRequest):
    form = CategoryForm(request.POST, instance=Category)
    if form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect('category_list')
    return render(request, 'inventory/category_form.html', {'form':form})

@login_required
@permission_required('inventory.delete_product', raise_exception=True)
def product_delete(request:HttpRequest, category_id:int):
    category = Product.objects.get(pk = category_id)
    category.delete()
    messages.success(request, "Category deleted successfully")
    return redirect('category_list')





#Supplier
@login_required
def product_list(request:HttpRequest):
    query = request.GET.get('q')
    suppliers = Supplier.objects.all()
    if query:
        supplier = suppliers.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query) | Q(suppliers__name__icontains=query)
        ).distinct()
    paginator = Paginator(supplier, 10)
    page = request.GET.get('page')
    suppliers =  paginator.GET.get_page(page)
    return render(request, 'inventory/supplier_list.html', {'suppliers':suppliers})


@login_required
@permission_required('inventory.add_supplier', raise_exception=True)
def supplier_create(request:HttpRequest):
    form = SupplierForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Supplier added successfully.")
        return redirect('supplier_list')
    return render(request, 'inventory/supplier_form.html', {'form':form})




@login_required
@permission_required('inventory.change_supplier', raise_exception=True)
def supplier_update(request:HttpRequest):
    form = SupplierForm(request.POST, instance=Supplier)
    if form.is_valid():
        form.save()
        messages.success(request, "Supplier updated successfully.")
        return redirect('supplier_list')
    return render(request, 'inventory/supplier_form.html', {'form':form})

@login_required
@permission_required('inventory.supplier_product', raise_exception=True)
def product_delete(request:HttpRequest, supplier_id:int):
    supplier = Product.objects.get(pk = supplier_id)
    supplier.delete()
    messages.success(request, "Supplier deleted successfully")
    return redirect('supplier_list')