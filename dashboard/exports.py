import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.utils import timezone
from datetime import datetime, timedelta
from sales.models import Order
from inventory.models import Inventory

@login_required
def export_sales_report(request):
    # Get date range from request parameters
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')

    try:
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = timezone.now()

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = end_date - timedelta(days=30)
    except ValueError:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

    # Query orders within date range
    orders = Order.objects.filter(
        order_date__range=(start_date, end_date)
    ).select_related('customer')

    # Create the HttpResponse object with CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="sales_report_{start_date.strftime("%Y%m%d")}-{end_date.strftime("%Y%m%d")}.csv"'},
    )

    # Create the CSV writer
    writer = csv.writer(response)
    writer.writerow([
        'Order Date', 'Order Number', 'Customer Name', 
        'Total Items', 'Total Price', 'Status'
    ])

    # Write data rows
    for order in orders:
        writer.writerow([
            order.order_date.strftime('%Y-%m-%d %H:%M'),
            order.order_number,
            order.customer.full_name,
            order.total_items,
            order.total_price,
            order.status
        ])

    return response

@login_required
def export_inventory_report(request):
    # Get filter parameters
    category_id = request.GET.get('category')
    stock_status = request.GET.get('stock_status')

    # Base query
    inventory_query = Inventory.objects.select_related('product', 'product__category')

    # Apply filters
    if category_id:
        inventory_query = inventory_query.filter(product__category_id=category_id)

    if stock_status == 'low':
        inventory_query = inventory_query.filter(
            current_stock__lte=F('low_stock_threshold'),
            current_stock__gt=0
        )
    elif stock_status == 'out':
        inventory_query = inventory_query.filter(current_stock=0)
    elif stock_status == 'normal':
        inventory_query = inventory_query.filter(current_stock__gt=F('low_stock_threshold'))

    # Create the HttpResponse object with CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="inventory_report_{timezone.now().strftime("%Y%m%d")}.csv"'},
    )

    # Create the CSV writer
    writer = csv.writer(response)
    writer.writerow([
        'Product', 'Category', 'Current Stock',
        'Low Stock Threshold', 'Unit Price', 'Total Value', 'Status'
    ])

    # Write data rows
    for item in inventory_query:
        total_value = item.current_stock * item.product.price
        if item.current_stock == 0:
            status = 'Out of Stock'
        elif item.current_stock <= item.low_stock_threshold:
            status = 'Low Stock'
        else:
            status = 'Normal'

        writer.writerow([
            item.product.name,
            item.product.category.name,
            item.current_stock,
            item.low_stock_threshold,
            item.product.price,
            total_value,
            status
        ])

    return response
