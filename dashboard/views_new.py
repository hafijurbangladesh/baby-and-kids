import csv
from django.http import HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q, Avg
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone
from django.core.paginator import Paginator
from sales.models import Order, OrderItem, Transaction
from inventory.models import Inventory, Product, Category
from accounts.models import Customer

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Sales Overview
        context.update(self.get_sales_metrics(start_of_day, start_of_week, start_of_month))
        
        # Inventory Insights
        context.update(self.get_inventory_insights())
        
        # Customer Metrics
        context.update(self.get_customer_metrics(start_of_month))
        
        # Charts Data
        context.update(self.get_charts_data(start_of_month))
        
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

    def get_charts_data(self, start_of_month):
        # Daily sales trend
        daily_sales = Order.objects.filter(
            status='completed',
            order_date__gte=start_of_month
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total_sales=Sum('total'),
            order_count=Count('id')
        ).order_by('date')

        # Sales by hour (for optimal hours analysis)
        hourly_sales = Order.objects.filter(
            status='completed'
        ).annotate(
            hour=ExtractHour('order_date')
        ).values('hour').annotate(
            avg_sales=Avg('total'),
            order_count=Count('id')
        ).order_by('hour')

        # Payment method distribution
        payment_methods = Transaction.objects.filter(
            order__status='completed'
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('amount_paid')
        )

        # Category performance
        category_sales = OrderItem.objects.filter(
            order__status='completed'
        ).values(
            'product__category__name'
        ).annotate(
            total_sales=Sum(F('quantity') * F('price')),
            quantity_sold=Sum('quantity')
        ).order_by('-total_sales')

        return {
            'daily_sales': list(daily_sales),
            'hourly_sales': list(hourly_sales),
            'payment_methods': list(payment_methods),
            'category_sales': list(category_sales)
        }
