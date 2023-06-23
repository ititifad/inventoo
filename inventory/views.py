from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from .forms import StockForm
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from datetime import date, timedelta, datetime
from django.db.models.functions import Coalesce
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from .decorators import super_admin_required


@login_required
@super_admin_required
def homepage(request):
    sales = Sale.objects.all().order_by('-sale_date')[:5]
    purchases = Purchase.objects.all().order_by('-purchase_date')[:5]
    
    geita_store_stock = Stock.objects.filter(store__name='Geita Store').aggregate(sum=Sum('quantity'))['sum']
    mwanza_store_stock = Stock.objects.filter(store__name='Mwanza Store').aggregate(sum=Sum('quantity'))['sum']

    total_purchase_value = Purchase.objects.aggregate(
        total_value=ExpressionWrapper(
            Sum(F('quantity') * F('unit_price')),
            output_field=DecimalField()
        )
    )['total_value']

    store_purchases = Purchase.objects.values('store__name').annotate(total_purchase_value=Sum(models.F('unit_price') * models.F('quantity')))

    total_sales_value = Sale.objects.aggregate(
        total_value=ExpressionWrapper(
            Sum(F('quantity') * F('unit_price')),
            output_field=DecimalField()
        )
    )['total_value']

    

    # total_profit = total_sales_value - total_purchase_value

    context = {
        'sales':sales,
        'purchases':purchases,
        'geita_store_stock':geita_store_stock,
        'mwanza_store_stock':mwanza_store_stock,
        'total_purchase_value':total_purchase_value,
        'total_sales_value':total_sales_value,
        # 'total_profit':total_profit,
        'store_purchases':store_purchases
    }
    
    return render(request, 'inventory/homepage.html', context)

@login_required
@super_admin_required
def store_list(request):
    
    stores = Store.objects.all()
    return render(request, 'inventory/store_list.html', {'stores': stores})


@login_required
@super_admin_required
def products(request):
    
    products = Stock.objects.all()
    return render(request, 'inventory/products.html', {'products': products})


@login_required
@super_admin_required
def product_list(request, store_id):
    stores = Store.objects.get(pk=store_id)
    products = Product.objects.filter(stores=stores)
    return render(request, 'inventory/product_list.html', {'stores': stores, 'products': products})

@login_required
@super_admin_required
def purchase_product(request, store_id, product_id):
    store = Store.objects.get(pk=store_id)
    product = Product.objects.get(pk=product_id)
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        supplier_id = request.POST['supplier']
        quantity = int(request.POST['quantity'])
        supplier = Supplier.objects.get(pk=supplier_id)

        Purchase.objects.create(product=product, supplier=supplier, quantity=quantity)
        product.stock += quantity
        product.save()

        # Calculate total price after purchase
        total_price = product.price * quantity

        messages.success(request, f'Product has been successfuly Purchased!')
        return redirect('product_list', store_id=store.id)

    return render(request, 'inventory/purchase_product.html', {'store': store, 'product': product, 'suppliers': suppliers})


@login_required
@super_admin_required
def sell_product(request, store_id, product_id):
    store = Store.objects.get(id=store_id)
    product = Product.objects.get(id=product_id)

    if request.method == 'POST':
        quantity = int(request.POST['quantity'])

        if product.stock < quantity:
            return render(request, 'inventory/sell_product.html', {'store': store, 'product': product, 'error': 'Insufficient stock'})

        sale = Sale.objects.create(
            product=product,
            quantity=quantity
        )

        # Update stock after sale
        product.stock -= quantity
        product.save()

        # Calculate total price after sale
        total_price = product.price * quantity

        return render(request, 'inventory/sell_product.html', {'store': store, 'product': product, 'total_price': total_price})

    return render(request, 'inventory/sell_product.html', {'store': store, 'product': product})



@login_required
@super_admin_required
def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    purchases = Purchase.objects.filter(product=product)
    sales = Sale.objects.filter(product=product)
    context = {'product': product, 'purchases': purchases, 'sales': sales}
    return render(request, 'inventory/product_detail.html', context)

# Add views for purchase and sale transactions, and bill generation


@login_required
@super_admin_required
def stock_data(request):
    stocks = Stock.objects.all()
    labels = []
    quantity = []

    for stock in stocks:
        labels.append(stock.product.name)
        quantity.append(stock.quantity)

    return JsonResponse({'labels': labels, 'quantity': quantity})



@login_required
@super_admin_required
def calculate_profit_loss(request, store_id):
    store = Store.objects.get(pk=store_id)
    purchases = Purchase.objects.filter(store=store)
    sales = Sale.objects.filter(store=store)
    stock = Stock.objects.filter(store=store)

    # Calculate total purchases
    total_purchases = sum(p.quantity * p.unit_price for p in purchases)

    # Calculate total sales
    total_sales = sum(s.quantity * s.unit_price for s in sales)

    # Calculate total current stock value
    stock_value = sum(s.quantity * s.product.price for s in stock)

    # Calculate profit/loss
    profit_loss = total_sales - total_purchases

    context = {
        'store': store,
        'purchases': purchases,
        'sales': sales,
        'stock': stock,
        'total_purchases': total_purchases,
        'total_sales': total_sales,
        'stock_value': stock_value,
        'profit_loss': profit_loss,
    }

    html = render_to_string('inventory/profit_loss.html', context)
    return HttpResponse(html)


@login_required
@super_admin_required
def add_purchased_product(request):
    if request.method == 'POST':
        # Retrieve form data
        store_id = request.POST['store']
        product_id = request.POST['product']
        supplier_id = request.POST['supplier']
        quantity = int(request.POST['quantity'])
        unit_price = float(request.POST['unit_price'])

        # Create new purchase record
        store = Store.objects.get(pk=store_id)
        product = Product.objects.get(pk=product_id)
        supplier = Supplier.objects.get(pk=supplier_id)
        purchase = Purchase(store=store, product=product, supplier=supplier, quantity=quantity, unit_price=unit_price)
        purchase.save()

        # Update stock quantity
        stock, created = Stock.objects.get_or_create(store=store, product=product)
        stock.quantity += quantity
        stock.save()

        messages.success(request, f'Stock has been successfuly Added!')
        return redirect('store_list')

    stores = Store.objects.all()
    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/add_purchased_product.html', {'stores': stores, 'products': products, 'suppliers': suppliers})


@login_required
@super_admin_required
def add_sold_product(request):
    if request.method == 'POST':
        # Retrieve form data
        store_id = request.POST['store']
        product_id = request.POST['product']
        quantity = int(request.POST['quantity'])
        unit_price = float(request.POST['unit_price'])

        # Create new sale record
        store = Store.objects.get(pk=store_id)
        product = Product.objects.get(pk=product_id)
        sale = Sale(store=store, product=product, quantity=quantity, unit_price=unit_price)
        sale.save()

        # Update stock quantity
        stock = Stock.objects.get(store=store, product=product)
        stock.quantity -= quantity
        stock.save()

        messages.success(request, f'Product has been successfuly sold!')

        return redirect('store_list')

    stores = Store.objects.all()
    products = Product.objects.all()
    return render(request, 'inventory/add_sold_product.html', {'stores': stores, 'products': products})


@login_required
@super_admin_required
def add_stock(request):
    if request.method == 'POST':
        store_id = request.POST['store']
        product_id = request.POST['product']
        quantity = int(request.POST['quantity'])

        store = Store.objects.get(id=store_id)
        product = Product.objects.get(id=product_id)

        stock, created = Stock.objects.get_or_create(store=store, product=product)
        stock.quantity += quantity
        stock.save()

        return redirect('stock_list')

    stores = Store.objects.all()
    products = Product.objects.all()
    # if request.method == 'POST':
    #     form = StockForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, f'Stock has been successfuly Added!')
    #         return redirect('products')  # Redirect to the stock list view
    # else:
    #     form = StockForm()
    return render(request, 'inventory/add_stock.html', {'stores': stores, 'products': products})



@login_required
@super_admin_required
def update_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, f'Stock has been successfuly Update!')
            return redirect('products')  # Redirect to the stock list view
    else:
        form = StockForm(instance=stock)
    return render(request, 'inventory/update_stock.html', {'form': form})



@login_required
@super_admin_required
def delete_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    if request.method == 'POST':
        stock.delete()
        messages.error(request, f'Stock has been successfuly Deleted!')
        return redirect('products')  # Redirect to the stock list view
    return render(request, 'inventory/delete_stock.html', {'stock': stock})



@login_required
@super_admin_required
def sales_report(request):
    target_date = date.today()
    start_date = date.today() - timedelta(days=7)
    month_date = date.today().replace(day=1)
    year_date = date.today().replace(month=1, day=1)
    end_date = date.today()

    #daily sales + profit
    daily_sales = Sale.objects.filter(sale_date=target_date).aggregate(total_sales=Sum(models.F('unit_price') * models.F('quantity')))['total_sales']
    daily_profit = Sale.objects.filter(sale_date=target_date).aggregate(total_profit=Sum(models.F('unit_price') * models.F('quantity')) - Sum(models.F('product__price') * models.F('quantity')))['total_profit']

    #weekly sales and profit
    weekly_sales = Sale.objects.filter(sale_date__range=[start_date, end_date]).aggregate(total_sales=Sum(models.F('unit_price') * models.F('quantity')))['total_sales']
    weekly_profit = Sale.objects.filter(sale_date__range=[start_date, end_date]).aggregate(total_profit=Sum(models.F('unit_price') * models.F('quantity')) - Sum(models.F('product__price') * models.F('quantity')))['total_profit']

    #monthly sales and profit
    monthly_sales = Sale.objects.filter(sale_date__range=[month_date, end_date]).aggregate(total_sales=Sum(models.F('unit_price') * models.F('quantity')))['total_sales']
    monthly_profit = Sale.objects.filter(sale_date__range=[month_date, end_date]).aggregate(total_profit=Sum(models.F('unit_price') * models.F('quantity')) - Sum(models.F('product__price') * models.F('quantity')))['total_profit']

    #yearly sales and profits
    yearly_sales = Sale.objects.filter(sale_date__range=[year_date, end_date]).aggregate(total_sales=Sum(models.F('unit_price') * models.F('quantity')))['total_sales']
    yearly_profit = Sale.objects.filter(sale_date__range=[year_date, end_date]).aggregate(total_profit=Sum(models.F('unit_price') * models.F('quantity')) - Sum(models.F('product__price') * models.F('quantity')))['total_profit']

    context = {
        'daily_sales':daily_sales,
        'daily_profit':daily_profit,
        'weekly_sales':weekly_sales,
        'weekly_profit':weekly_profit,
        'monthly_sales':monthly_sales,
        'monthly_profit':monthly_profit,
        'yearly_sales':yearly_sales,
        'yearly_profit':yearly_profit
    }

    return render(request, 'inventory/sales_reports.html', context)



@login_required
@super_admin_required
def purchase_report(request):

    today = date.today()

    # Calculate the start and end dates for the week
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

        # Calculate the start and end dates for the month
    start_of_month = date(today.year, today.month, 1)
    end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # Calculate the start and end dates for the year
    start_of_year = date(today.year, 1, 1)
    end_of_year = date(today.year, 12, 31)

        # Retrieve the total monetary value for each store
    store_totals = Purchase.objects.values('store').annotate(total=Sum('unit_price') * Sum('quantity'))

        # Retrieve the total purchases for a day, week, month, and year
    day_total = Purchase.objects.filter(purchase_date=today).aggregate(total=Sum('unit_price') * Sum('quantity'))
    week_total = Purchase.objects.filter(purchase_date__range=(start_of_week, end_of_week)).aggregate(total=Sum('unit_price') * Sum('quantity'))
    month_total = Purchase.objects.filter(purchase_date__range=(start_of_month, end_of_month)).aggregate(total=Sum('unit_price') * Sum('quantity'))
    year_total = Purchase.objects.filter(purchase_date__range=(start_of_year, end_of_year)).aggregate(total=Sum('unit_price') * Sum('quantity'))

    context = {
            'store_totals': store_totals,
            'day_total': day_total,
            'week_total': week_total,
            'month_total': month_total,
            'year_total': year_total
        }    

    return render(request, 'inventory/sales_report.html', context)


@login_required
@super_admin_required
def store_purchases(request):
    # Calculate total monetary value for each store
    store_totals = Purchase.objects.values('store__name').annotate(total_value=Sum(F('quantity') * F('unit_price')))

    # Calculate total purchases for a day, week, month, and year
    today = date.today()
    day_total = Purchase.objects.filter(purchase_date=today).aggregate(total=Sum('quantity'))
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    week_total = Purchase.objects.filter(purchase_date__range=(week_start, week_end)).aggregate(total=Sum('quantity'))
    month_start = today.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    month_total = Purchase.objects.filter(purchase_date__range=(month_start, month_end)).aggregate(total=Sum('quantity'))
    year_start = today.replace(month=1, day=1)
    year_end = today.replace(month=12, day=31)
    year_total = Purchase.objects.filter(purchase_date__range=(year_start, year_end)).aggregate(total=Sum('quantity'))

    context = {
        'store_totals': store_totals,
        'day_total': day_total,
        'week_total': week_total,
        'month_total': month_total,
        'year_total': year_total
    }

    return render(request, 'inventory/summary.html', context)


# def inventory_value_report(request):
#     # Retrieve all stores
#     stores = Store.objects.all()

#     # Calculate the total inventory value for each store
#     store_inventory_values = Stock.objects.values('store').annotate(
#         inventory_value=Sum(F('quantity') * F('product__price'))
#     )

#     # Pass the data to the template for rendering
#     context = {
#         'stores': stores,
#         'store_inventory_values': store_inventory_values
#     }
#     return render(request, 'inventory/inventory_value_report.html', context)


@login_required
@super_admin_required
def inventory_value_report(request):
    # Retrieve the total value of each product in stock
    inventory = Stock.objects.annotate(
        total_value=F('quantity') * F('product__price')
    ).values('product__name', 'total_value')

    # Calculate the overall inventory value
    total_inventory_value = Stock.objects.aggregate(
        total_value=Sum(F('quantity') * F('product__price'))
    )['total_value']

    context = {
        'inventory': inventory,
        'total_inventory_value': total_inventory_value,
    }

    return render(request, 'inventory/inventory_value_report.html', context)



@login_required
@super_admin_required
def sales_report_by_store(request):
    stores = Store.objects.all()
    data = []
    
    for store in stores:
        sales = Sale.objects.filter(store=store)
        total_quantity = sales.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
        total_revenue = sales.aggregate(total_revenue=Sum(F('quantity') * F('unit_price')))['total_revenue'] or 0
        data.append({
            'store': store,
            'total_quantity': total_quantity,
            'total_revenue': total_revenue
        })
    
    context = {
        'data': data
    }
    
    return render(request, 'inventory/sales_report_by_store.html', context)



@login_required
@super_admin_required
def product_stock_report(request):
    # Retrieve all stores and their associated stock information
# Retrieve the relevant data for the report
    stock_items = Stock.objects.all()

    # Pass the data to the template for rendering
    return render(request, 'inventory/product_stock_report.html', {'stock_items': stock_items})

def supplier_purchase_history(request):
    suppliers = Supplier.objects.all()
    purchase_history = []

    for supplier in suppliers:
        purchases = Purchase.objects.filter(supplier=supplier)
        purchase_history.append({
            'supplier': supplier,
            'purchases': purchases
        })

    return render(request, 'inventory/supplier_purchase_history.html', {'purchase_history': purchase_history})