from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.db.models import Sum, Count, F, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
import csv

from sales.models import Order, OrderItem
from inventory.models import Product, Category

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
        })

        # Handle CSV export
        if self.request.GET.get('export') == 'csv':
            return self.export_to_csv(orders)

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
            total=Sum('total_price')
        ).order_by('date')

        dates = [item['date'].strftime('%Y-%m-%d') for item in sales_by_date]
        sales = [float(item['total']) for item in sales_by_date]

        return {
            'dates': dates,
            'sales': sales
        }

    def get_category_sales(self, orders):
        category_sales = OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__category__name'
        ).annotate(
            total=Sum(F('quantity') * F('unit_price'))
        ).order_by('-total')

        categories = [item['product__category__name'] for item in category_sales]
        amounts = [float(item['total']) for item in category_sales]

        return {
            'categories': categories,
            'amounts': amounts
        }

    def get_top_products(self, orders):
        return OrderItem.objects.filter(
            order__in=orders
        ).values(
            'product__name'
        ).annotate(
            quantity=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-revenue')[:10]

    def export_to_csv(self, orders):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Order ID', 'Customer', 'Items', 'Total', 
            'Payment Method', 'Status'
        ])

        for order in orders:
            writer.writerow([
                order.order_date.strftime('%Y-%m-%d %H:%M'),
                order.id,
                order.customer.name,
                order.orderitem_set.count(),
                order.total_price,
                order.transaction.get_payment_method_display(),
                order.get_status_display()
            ])

        return response
