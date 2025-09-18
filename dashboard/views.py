from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum, Count, Avg, F, Q, Max
from django.db.models.functions import TruncDate, TruncHour, Coalesce
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView
from accounts.models import Customer
from inventory.models import Product, Inventory
from sales.models import Order, OrderItem
import csv
import json


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = today - timedelta(days=30)

        # Get all required metrics
        sales_metrics = self.get_sales_metrics(start_of_day, start_of_week, start_of_month)
        inventory_insights = self.get_inventory_insights()
        customer_metrics = self.get_customer_metrics(start_of_month)
        charts_data = self.get_charts_data(thirty_days_ago)
        
        # Get recent orders
        recent_orders = Order.objects.filter(
            status='completed'
        ).select_related('customer').order_by('-order_date')[:5]

        # Calculate inventory value
        inventory_value = Product.objects.aggregate(
            total_value=Sum(F('inventory__quantity') * F('price'))
        )['total_value'] or Decimal('0.00')

        context.update({
            'sales_summary': {
                'today_sales': sales_metrics['today']['total_sales'],
                'week_sales': sales_metrics['week']['total_sales'],
                'total_orders': sales_metrics['month']['order_count'],
            },
            'inventory_summary': {
                'total_value': inventory_value,
                'low_stock_count': len(inventory_insights['low_stock_products']),
                'out_of_stock_count': inventory_insights['out_of_stock_count'],
            },
            'recent_orders': recent_orders,
            'low_stock_products': inventory_insights['low_stock_products'],
            'top_products': self.get_top_selling_products(thirty_days_ago),
            'recent_customers': Customer.objects.filter(
                order__status='completed'
            ).annotate(
                total_orders=Count('order'),
                total_spending=Sum('order__total'),
                last_order_date=Max('order__order_date')
            ).order_by('-last_order_date')[:5],
            'charts_data': charts_data
        })
        
        return context

    def get_sales_metrics(self, start_of_day, start_of_week, start_of_month):
        # Base queryset for completed orders
        completed_orders = Order.objects.filter(status='completed')

        # Today's metrics
        today_metrics = completed_orders.filter(
            order_date__gte=start_of_day
        ).aggregate(
            total_sales=Coalesce(Sum('total'), Decimal('0.00')),
            order_count=Count('id'),
            avg_order_value=Coalesce(Avg('total'), Decimal('0.00'))
        )

        # Week metrics
        week_metrics = completed_orders.filter(
            order_date__gte=start_of_week
        ).aggregate(
            total_sales=Coalesce(Sum('total'), Decimal('0.00')),
            order_count=Count('id'),
            avg_order_value=Coalesce(Avg('total'), Decimal('0.00'))
        )

        # Month metrics
        month_metrics = completed_orders.filter(
            order_date__gte=start_of_month
        ).aggregate(
            total_sales=Coalesce(Sum('total'), Decimal('0.00')),
            order_count=Count('id'),
            avg_order_value=Coalesce(Avg('total'), Decimal('0.00'))
        )

        return {
            'today': today_metrics,
            'week': week_metrics,
            'month': month_metrics
        }

    def get_inventory_insights(self):
        # Get low stock products (where quantity is below threshold)
        low_stock_products = Product.objects.filter(
            inventory__quantity__lte=F('inventory__low_stock_threshold')
        ).select_related('inventory')[:5]

        # Get top selling products
        top_selling = OrderItem.objects.values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-total_quantity')[:5]

        # Get out of stock count
        out_of_stock_count = Product.objects.filter(
            inventory__quantity=0
        ).count()

        return {
            'low_stock_products': low_stock_products,
            'top_selling': top_selling,
            'out_of_stock_count': out_of_stock_count
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

        # Calculate retention rate
        total_customers = Customer.objects.count()
        if total_customers > 0:
            repeat_customers = Order.objects.filter(
                status='completed'
            ).values('customer').annotate(
                order_count=Count('id')
            ).filter(order_count__gt=1).count()
            
            retention_rate = (repeat_customers / total_customers) * 100
        else:
            retention_rate = 0

        return {
            'new_customers': new_customers,
            'top_customers': top_customers,
            'retention_rate': retention_rate
        }

    def get_top_selling_products(self, thirty_days_ago):
        """Get top selling products for the last 30 days"""
        return OrderItem.objects.filter(
            order__status='completed',
            order__order_date__gte=thirty_days_ago
        ).values(
            'product__name',
            'product__sku',
            'product__category__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum(F('quantity') * F('price'))
        ).order_by('-total_quantity')[:5]

    def get_charts_data(self, thirty_days_ago):
        # Daily sales trend for the last 30 days
        daily_sales = Order.objects.filter(
            status='completed',
            order_date__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total_sales=Coalesce(Sum('total'), Decimal('0.00')),
            order_count=Count('id')
        ).order_by('date')

        # If there are missing dates in the range, fill them with zeros
        all_dates = []
        current_date = thirty_days_ago.date()
        end_date = timezone.now().date()
        
        # Create a dictionary of existing sales data
        sales_dict = {item['date']: item for item in daily_sales}
        
        # Fill in all dates
        while current_date <= end_date:
            if current_date in sales_dict:
                all_dates.append(sales_dict[current_date])
            else:
                all_dates.append({
                    'date': current_date,
                    'total_sales': Decimal('0.00'),
                    'order_count': 0
                })
            current_date += timedelta(days=1)

        # Category performance
        category_sales = OrderItem.objects.filter(
            order__status='completed',
            order__order_date__gte=thirty_days_ago
        ).values(
            'product__category__name'
        ).annotate(
            total_sales=Coalesce(Sum(F('quantity') * F('price')), Decimal('0.00')),
            quantity_sold=Sum('quantity')
        ).order_by('-total_sales')

        # Convert Decimal objects to float for JSON serialization
        daily_sales_data = [{
            'date': item['date'].isoformat(),
            'total_sales': float(item['total_sales']),
            'order_count': item['order_count']
        } for item in all_dates]

        category_sales_data = [{
            'product__category__name': item['product__category__name'] or 'Uncategorized',
            'total_sales': float(item['total_sales']),
            'quantity_sold': item['quantity_sold']
        } for item in category_sales]

        return {
            'daily_sales': daily_sales_data,
            'category_sales': category_sales_data
        }


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

        # Generate all report data
        summary = self.get_sales_summary(orders)
        sales_trend_data = self.get_sales_trend(orders, report_type)
        category_sales_data = self.get_category_sales(orders)
        top_products = self.get_top_products(orders)

        # Prepare category sales data for the chart
        category_data = {
            'categories': json.dumps([item['product__category__name'] or 'Uncategorized' for item in category_sales_data]),
            'amounts': json.dumps([float(item['total_sales']) for item in category_sales_data])
        }

        context.update({
            'summary': summary,
            'sales_trend': {
                'dates': json.dumps(sales_trend_data['labels']),
                'sales': json.dumps(sales_trend_data['data'])
            },
            'category_sales': category_data,
            'top_products': top_products,
            'orders': orders[:50],  # Limit to last 50 orders
            'report_type': report_type,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })

        return context

    def get_sales_summary(self, orders):
        """Generate summary metrics for sales report"""
        items_sold = OrderItem.objects.filter(
            order__in=orders
        ).aggregate(total=Coalesce(Sum('quantity'), 0))['total']

        summary = orders.aggregate(
            total_sales=Coalesce(Sum('total'), Decimal('0.00')),
            total_orders=Count('id'),
            avg_order_value=Coalesce(Avg('total'), Decimal('0.00'))
        )
        summary['items_sold'] = items_sold
        return summary

    def get_sales_trend(self, orders, report_type):
        """Generate sales trend data based on report type"""
        # Get start and end dates from orders or request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = timezone.now() - timedelta(days=30)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = timezone.now()

        # Set up time truncation based on report type
        if report_type == 'hourly':
            trunc_func = TruncHour('order_date')
            format_str = '%Y-%m-%d %H:00'
            delta = timedelta(hours=1)
            current = timezone.localtime(start_date).replace(minute=0, second=0, microsecond=0)
            end = timezone.localtime(end_date)
        else:  # daily
            trunc_func = TruncDate('order_date')
            format_str = '%Y-%m-%d'
            delta = timedelta(days=1)
            current = start_date.date()
            end = end_date.date()

        # Get sales data
        sales_data = orders.annotate(
            period=trunc_func
        ).values('period').annotate(
            total=Coalesce(Sum('total'), Decimal('0.00')),
            count=Count('id')
        ).order_by('period')

        # Create a dictionary of existing data
        data_dict = {x['period']: x for x in sales_data}
        
        # Fill in all periods with data or zeros
        all_periods = []
        while current <= end:
            if current in data_dict:
                all_periods.append({
                    'period': current,
                    'total': float(data_dict[current]['total']),
                    'count': data_dict[current]['count']
                })
            else:
                all_periods.append({
                    'period': current,
                    'total': 0.0,
                    'count': 0
                })
            current += delta

        return {
            'labels': [p['period'].strftime(format_str) for p in all_periods],
            'data': [p['total'] for p in all_periods],
            'counts': [p['count'] for p in all_periods]
        }

    def get_category_sales(self, orders):
        """Generate category-wise sales data"""
        return OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__category__name'
        ).annotate(
            total_sales=Coalesce(Sum(F('quantity') * F('price')), Decimal('0.00')),
            quantity_sold=Sum('quantity')
        ).order_by('-total_sales')

    def get_top_products(self, orders):
        """Get top selling products for the period"""
        return OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__name', 
            'product__sku'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Coalesce(Sum(F('quantity') * F('price')), Decimal('0.00'))
        ).order_by('-total_quantity')[:10]


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
            order.transaction.payment_method if hasattr(order, 'transaction') else 'N/A',
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
