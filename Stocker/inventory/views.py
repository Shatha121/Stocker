from django.shortcuts import render , redirect
from django.http import HttpRequest, HttpResponse
from .models import Product, Category, Supplier, StockUpdate
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
@permission_required('inventory.change_product', raise_exception=True)
def update_stock(request:HttpRequest, product_id:int):
    product = Product.objects.get(pk = product_id)
    if request.method == 'POST':
        try:
            quantity_change = int(request.POST.get('quantity_change'))
        except:
            messages.error(request,"Invaild quantity.")
            return redirect('inventory:update_stock', product_id=product.id)
        
        product.quantity_in_stock += quantity_change
        if product.quantity_in_stock < 0 :
            messages.error(request, "Resulting stock can't be negative.")
            return redirect('inventory:update_stock', product_id=product.id)
        
        product.save()
        
        StockUpdate.objects.create(
            product=product,
            updated_by = request.user,
            quantity_change = quantity_change,
            note=request.POST.get('note','')
        )
        messages.success(request, "Stock updated successfully.")
        return redirect('inventory:product_list')
    return render(request, 'inventory/stock_update.html', {'product':product})



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
        products = products.filter(category_id=category)
    if supplier:
        products = products.filter(supplier_id=supplier)
    paginator = Paginator(products, 10)
    page = request.GET.get('page')
    products =  paginator.get_page(page)
    context = {
        "products": products,
        "categories": Category.objects.all(),
        "suppliers": Supplier.objects.all(),
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
@permission_required('inventory.add_product', raise_exception=True)
def product_add(request:HttpRequest):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        supplier_ids = request.POST.getlist('supplier')
        quantity_in_stock = request.POST.get('quantity')
        expiry_date = request.POST.get('expiry_date')
        image = request.FILES.get('image')

        category = Category.objects.get(id=category_id)
        product = Product.objects.create(
            name=name,
            description = description,
            price = price,
            category=category,
            quantity_in_stock = quantity_in_stock,
            expiry_date = expiry_date if expiry_date else None,
            image = image
        )
        if supplier_ids:
            product.suppliers.set(supplier_ids)

        messages.success(request, "Product added successfully")
        return redirect('product_list')
    
    return render(request, 'inventory/product_add.html', {'categories':Category.objects.all(), 'suppliers':Supplier.objects.all(),})


@login_required
def product_detail(request, product_id:int):
    product = Product.objects.get(pk = product_id)
    return render(request, 'inventory/product_detail.html', {'product':product})


@login_required
@permission_required('inventory.change_product', raise_exception=True)
def product_update(request:HttpRequest, product_id:int):
    product = Product.objects.get(pk = product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.category_id = request.POST.get('category')
        product.quantity_in_stock = request.POST.get('quantity')
        product.expiry_date = request.POST.get('expiry_date') or None

        if 'image' in request.FILES:
            product.image = request.FILES['image'] 
        
        product.save()
        product.suppliers.set(request.POST.getlist('suppliers'))

        messages.success(request, "Product updated successfully.")
        return redirect('inventory:product_list')
    
    context = {
        'product': product,
        'category_choices': [(c.id, c.name) for c in Category.objects.all()],
        'suppliers': Supplier.objects.all(),
    }

    return render(request, 'inventory/product_update.html', context)

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
        category = categories.filter(name__icontains=query)
    paginator = Paginator(category, 10)
    page = request.GET.get('page')
    categories =  paginator.get_page(page)
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
def category_update(request:HttpRequest, category_id:int):
    category = Category.objects.get(pk=category_id)
    form = CategoryForm(request.POST, instance=category)
    if form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect('category_list')
    return render(request, 'inventory/category_form.html', {'form':form})

@login_required
@permission_required('inventory.delete_category', raise_exception=True)
def category_delete(request:HttpRequest, category_id:int):
    category = Category.objects.get(pk = category_id)
    category.delete()
    messages.success(request, "Category deleted successfully")
    return redirect('category_list')





#Supplier
@login_required
def supplier_list(request:HttpRequest):
    query = request.GET.get('q')
    suppliers = Supplier.objects.all()
    if query:
        supplier = suppliers.filter(
            Q(name__icontains=query)
        ).distinct()
    paginator = Paginator(supplier, 10)
    page = request.GET.get('page')
    suppliers =  paginator.get_page(page)
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
def supplier_update(request:HttpRequest, supplier_id:int):
    supplier = Supplier.objects.get(pk = supplier_id)
    form = SupplierForm(request.POST, instance=supplier)
    if form.is_valid():
        form.save()
        messages.success(request, "Supplier updated successfully.")
        return redirect('supplier_list')
    return render(request, 'inventory/supplier_form.html', {'form':form})

@login_required
@permission_required('inventory.supplier_product', raise_exception=True)
def supplier_delete(request:HttpRequest, supplier_id:int):
    supplier = Supplier.objects.get(pk = supplier_id)
    supplier.delete()
    messages.success(request, "Supplier deleted successfully")
    return redirect('supplier_list')