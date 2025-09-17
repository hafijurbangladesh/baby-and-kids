from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F, Q, Avg
from django.db.models.functions import TruncDate, ExtractHour, Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.http import HttpResponse
import json
import csv
from sales.models import Order, OrderItem
from inventory.models import Product, Inventory
from accounts.models import Customer

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_charts_data(self):
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)

        # Daily sales trend
        daily_sales = Order.objects.filter(
            status='completed',
            order_date__date__gte=thirty_days_ago.date()
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total_sales=Coalesce(Sum('total'), 0)
        ).order_by('date')

        # Category distribution
        category_sales = OrderItem.objects.filter(
            order__status='completed',
            order__order_date__gte=thirty_days_ago
        ).values(
            'product__category__name'
        ).annotate(
            total_sales=Sum(F('quantity') * F('price'))
        ).order_by('-total_sales')[:5]

        return {
            'daily_sales': list(daily_sales),
            'category_sales': list(category_sales)
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)
        seven_days_ago = today - timedelta(days=7)

        print("Debug: Fetching dashboard data...")
        print(f"Date range: {thirty_days_ago} to {today}")

        # Basic Sales Summary with default values
        sales_summary = Order.objects.filter(
            status='completed'
        ).aggregate(
            today_sales=Coalesce(Sum('total', filter=Q(order_date__date=today.date())), Decimal('0.00')),
            week_sales=Coalesce(Sum('total', filter=Q(order_date__gte=seven_days_ago)), Decimal('0.00')),
            month_sales=Coalesce(Sum('total', filter=Q(order_date__gte=thirty_days_ago)), Decimal('0.00')),
            total_orders=Count('id', filter=Q(order_date__gte=thirty_days_ago))
        )

        # Daily sales for the chart
        daily_sales = Order.objects.filter(
            status='completed',
            order_date__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total_sales=Coalesce(Sum('total'), Decimal('0.00'))
        ).order_by('date')

        # Low stock products
        low_stock_products = Product.objects.select_related('inventory').filter(
            inventory__quantity__lte=F('inventory__low_stock_threshold')
        )[:5]

        # Top selling products
        top_products = OrderItem.objects.filter(
            order__status='completed',
            order__order_date__gte=thirty_days_ago
        ).values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity')
        ).order_by('-total_quantity')[:5]

        # Prepare context with basic metrics
        context.update({
            'sales_summary': sales_summary,
            'low_stock_products': low_stock_products,
            'top_products': top_products,
            'charts_data': json.dumps({
                'dates': [str(entry['date']) for entry in daily_sales],
                'sales': [float(entry['total_sales']) for entry in daily_sales]
            })
        })
        return context

class SalesReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/sales_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        report_type = self.request.GET.get('report_type', 'daily')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = timezone.now() - timedelta(days=30)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = timezone.now()

        # Get orders within date range
        orders = Order.objects.filter(
            order_date__gte=start_date,
            order_date__lte=end_date,
            status='completed'
        ).select_related('customer', 'transaction')

        # Generate summary metrics
        summary = self.get_sales_summary(orders)
        
        # Generate trend data
        sales_trend = self.get_sales_trend(orders, report_type)
        
        # Get category sales
        category_sales = self.get_category_sales(orders)
        
        # Get top products
        top_products = self.get_top_products(orders)

        context.update({
            'summary': summary,
            'sales_trend': sales_trend,
            'category_sales': category_sales,
            'top_products': top_products,
            'orders': orders[:50],  # Limit to last 50 orders
            'report_type': report_type,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })

        return context

    def get_sales_summary(self, orders):
        items_sold = OrderItem.objects.filter(
            order__in=orders
        ).aggregate(total=Sum('quantity'))['total'] or 0

        summary = orders.aggregate(
            total_sales=Sum('total') or 0,
            total_orders=Count('id'),
            avg_order_value=Avg('total') or 0
        )
        summary['items_sold'] = items_sold

        return summary

    def get_sales_trend(self, orders, report_type):
        sales_by_date = orders.annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total=Sum('total')
        ).order_by('date')

        dates = [item['date'].strftime('%Y-%m-%d') for item in sales_by_date]
        sales = [float(item['total']) for item in sales_by_date]

        return {
            'dates': dates,
            'sales': sales
        }

    def get_category_sales(self, orders):
        return OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__category__name'
        ).annotate(
            total=Sum(F('quantity') * F('price')),
            items_sold=Sum('quantity')
        ).order_by('-total')

    def get_top_products(self, orders):
        return OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__name',
            'product__sku'
        ).annotate(
            total=Sum(F('quantity') * F('price')),
            items_sold=Sum('quantity')
        ).order_by('-total')[:10]

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)
        seven_days_ago = today - timedelta(days=7)

        print("Debug: Fetching dashboard data...")
        print(f"Date range: {thirty_days_ago} to {today}")

        # Basic Sales Summary
        sales_summary = Order.objects.filter(
            status='completed'
        ).aggregate(
            today_sales=Coalesce(Sum('total', filter=Q(order_date__date=today.date())), Decimal('0.00')),
            week_sales=Coalesce(Sum('total', filter=Q(order_date__gte=seven_days_ago)), Decimal('0.00')),
            month_sales=Coalesce(Sum('total', filter=Q(order_date__gte=thirty_days_ago)), Decimal('0.00')),
            total_orders=Count('id', filter=Q(order_date__gte=thirty_days_ago))
        )

        # Charts Data
        context.update({
            'sales_summary': sales_summary,
            'charts_data': self.get_charts_data()
        })
        
        return context

    def get_sales_metrics(self, start_of_day, start_of_week, start_of_month):
        # Today's metrics
        today_orders = Order.objects.filter(
            order_date__gte=start_of_day,
            status='completed'
        )
        today_sales = today_orders.aggregate(
            total_sales=Sum('total') or Decimal('0.00'),
            order_count=Count('id'),
            avg_order_value=Avg('total')
        )

        # This week's metrics
        week_orders = Order.objects.filter(
            order_date__gte=start_of_week,
            status='completed'
        )
        week_sales = week_orders.aggregate(
            total_sales=Sum('total') or Decimal('0.00'),
            order_count=Count('id')
        )

        # This month's metrics
        month_orders = Order.objects.filter(
            order_date__gte=start_of_month,
            status='completed'
        )
        month_sales = month_orders.aggregate(
            total_sales=Sum('total') or Decimal('0.00'),
            order_count=Count('id')
        )

        return {
            'today_sales': today_sales,
            'week_sales': week_sales,
            'month_sales': month_sales
        }

    def get_inventory_insights(self):
        # Low stock products
        low_stock_products = Product.objects.filter(
            inventory__quantity__lte=F('inventory__low_stock_threshold')
        ).select_related('inventory')[:5]

        # Top selling products
        top_selling = OrderItem.objects.values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-total_quantity')[:5]

        # Out of stock products
        out_of_stock = Product.objects.filter(
            inventory__quantity=0
        ).count()

        return {
            'low_stock_products': low_stock_products,
            'top_selling_products': top_selling,
            'out_of_stock_count': out_of_stock
        }

    def get_customer_metrics(self, start_of_month):
        # New customers this month
        new_customers = Customer.objects.filter(
            created_at__gte=start_of_month
        ).count()

        # Top customers by revenue
        top_customers = Order.objects.filter(
            status='completed'
        ).values(
            'customer__name'
        ).annotate(
            total_spent=Sum('total'),
            order_count=Count('id')
        ).order_by('-total_spent')[:5]

        # Customer retention rate
        total_customers = Customer.objects.count()
        repeat_customers = Order.objects.filter(
            status='completed'
        ).values('customer').annotate(
            order_count=Count('id')
        ).filter(order_count__gt=1).count()

        retention_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0

        return {
            'new_customers': new_customers,
            'top_customers': top_customers,
            'retention_rate': retention_rate
        }

    def get_charts_data(self):
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)

        # Daily sales trend
        daily_sales = Order.objects.filter(
            status='completed',
            order_date__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total_sales=Sum('total'),
            order_count=Count('id')
        ).order_by('date')

        # Category performance
        category_sales = OrderItem.objects.filter(
            order__status='completed',
            order__order_date__gte=thirty_days_ago
        ).values(
            'product__category__name'
        ).annotate(
            total_sales=Sum(F('quantity') * F('price')),
            quantity_sold=Sum('quantity')
        ).order_by('-total_sales')

        return {
            'daily_sales': list(daily_sales),
            'category_sales': list(category_sales)
        }

class InventoryReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/inventory_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all products with their inventory
        products = Product.objects.select_related(
            'inventory', 'category', 'brand', 'supplier'
        ).all()

        # Get low stock products
        low_stock = products.filter(
            inventory__quantity__lte=F('inventory__low_stock_threshold')
        )

        # Get out of stock products
        out_of_stock = products.filter(inventory__quantity=0)

        # Calculate category totals
        category_totals = Product.objects.values(
            'category__name'
        ).annotate(
            total_items=Sum('inventory__quantity'),
            total_value=Sum(F('inventory__quantity') * F('price'))
        )

        context.update({
            'products': products,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'category_totals': category_totals,
        })

        return context

def export_sales_report(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = timezone.now() - timedelta(days=30)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = timezone.now()

    # Get orders
    orders = Order.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date,
        status='completed'
    ).select_related('customer', 'transaction')

    # Create the HttpResponse object with CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="sales_report.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow([
        'Order ID', 'Date', 'Customer', 'Items', 'Total',
        'Payment Method', 'Status'
    ])

    for order in orders:
        writer.writerow([
            order.id,
            order.order_date.strftime('%Y-%m-%d %H:%M'),
            order.customer.name if order.customer else 'Walk-in Customer',
            order.orderitem_set.count(),
            order.total,
            order.transaction.payment_method,
            order.status
        ])

    return response

def export_inventory_report(request):
    # Get all products with their inventory
    products = Product.objects.select_related(
        'inventory', 'category', 'brand', 'supplier'
    ).all()

    # Create the HttpResponse object with CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="inventory_report.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow([
        'SKU', 'Product Name', 'Category', 'Brand',
        'Current Stock', 'Low Stock Threshold', 'Price',
        'Total Value', 'Supplier'
    ])

    for product in products:
        writer.writerow([
            product.sku,
            product.name,
            product.category.name,
            product.brand.name,
            product.inventory.quantity,
            product.inventory.low_stock_threshold,
            product.price,
            product.price * product.inventory.quantity,
            product.supplier.name
        ])

    return response
