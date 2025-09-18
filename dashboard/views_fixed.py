from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F, Q, Avg
from django.db.models.functions import TruncDate, ExtractHour, Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import json
from sales.models import Order, OrderItem
from inventory.models import Product, Inventory
from accounts.models import Customer

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)
        seven_days_ago = today - timedelta(days=7)

        # Sales Summary
        sales_summary = Order.objects.filter(
            status='completed'
        ).aggregate(
            today_sales=Coalesce(Sum('total', filter=Q(order_date__date=today.date())), Decimal('0.00')),
            week_sales=Coalesce(Sum('total', filter=Q(order_date__gte=seven_days_ago)), Decimal('0.00')),
            month_sales=Coalesce(Sum('total', filter=Q(order_date__gte=thirty_days_ago)), Decimal('0.00')),
            total_orders=Count('id', filter=Q(order_date__gte=thirty_days_ago))
        )

        # Inventory Summary
        inventory_summary = Product.objects.filter(is_active=True).aggregate(
            total_products=Count('id'),
            total_value=Sum(F('inventory__quantity') * F('price'), default=Decimal('0.00'))
        )

        # Low stock and out of stock products
        low_stock_products = Product.objects.filter(
            is_active=True,
            inventory__quantity__lte=F('inventory__low_stock_threshold'),
            inventory__quantity__gt=0
        ).select_related('inventory')[:5]

        out_of_stock_count = Product.objects.filter(
            is_active=True,
            inventory__quantity=0
        ).count()

        # Recent orders
        recent_orders = Order.objects.filter(
            status='completed'
        ).select_related('customer').order_by('-order_date')[:5]

        # Top selling products
        top_products = OrderItem.objects.filter(
            order__status='completed',
            order__order_date__gte=thirty_days_ago
        ).values(
            'product__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        ).order_by('-total_quantity')[:5]

        # Daily sales trend for chart
        daily_sales = Order.objects.filter(
            status='completed',
            order_date__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total_sales=Coalesce(Sum('total'), Decimal('0.00'))
        ).order_by('date')

        # Category sales for chart
        category_sales = OrderItem.objects.filter(
            order__status='completed',
            order__order_date__gte=thirty_days_ago
        ).values(
            'product__category__name'
        ).annotate(
            total_sales=Sum(F('quantity') * F('price'))
        ).order_by('-total_sales')[:5]

        # Update context with all data
        context.update({
            'sales_summary': sales_summary,
            'inventory_summary': inventory_summary,
            'low_stock_products': low_stock_products,
            'out_of_stock_count': out_of_stock_count,
            'recent_orders': recent_orders,
            'top_products': top_products,
            'charts_data': json.dumps({
                'dates': [str(entry['date']) for entry in daily_sales],
                'sales': [float(entry['total_sales']) for entry in daily_sales]
            }),
            'category_data': json.dumps({
                'labels': [entry['product__category__name'] for entry in category_sales],
                'values': [float(entry['total_sales']) for entry in category_sales]
            })
        })
        
        return context
