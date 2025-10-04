from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import ShopAssistant
from sales.models import Order
import json


class ShopAssistantAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/shop_assistant_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date filters
        period = self.request.GET.get('period', 'monthly')
        end_date = timezone.now()
        
        if period == 'daily':
            start_date = end_date - timedelta(days=30)
            date_format = '%Y-%m-%d'
        elif period == 'weekly':
            start_date = end_date - timedelta(weeks=12)
            date_format = '%Y-W%U'
        else:  # monthly
            start_date = end_date - timedelta(days=365)
            date_format = '%Y-%m'
        
        # Shop assistant performance data
        assistants_performance = []
        for assistant in ShopAssistant.objects.filter(is_active=True):
            performance_data = assistant.get_performance_data(start_date, end_date)
            assistants_performance.append({
                'assistant': assistant,
                'data': performance_data
            })
        
        # Top performers
        top_performers = ShopAssistant.objects.filter(
            is_active=True,
            order__order_date__gte=start_date
        ).annotate(
            period_sales=Sum('order__total'),
            period_orders=Count('order')
        ).order_by('-period_sales')[:5]
        
        # Sales comparison data for charts
        chart_data = self.get_chart_data(start_date, end_date, date_format)
        
        context.update({
            'assistants_performance': assistants_performance,
            'top_performers': top_performers,
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'chart_data': json.dumps(chart_data),
        })
        
        return context
    
    def get_chart_data(self, start_date, end_date, date_format):
        """Generate chart data for assistant performance comparison"""
        assistants = ShopAssistant.objects.filter(is_active=True)
        chart_data = {
            'labels': [],
            'datasets': []
        }
        
        # Generate time periods
        current_date = start_date
        periods = []
        while current_date <= end_date:
            periods.append(current_date.strftime(date_format))
            if 'W' in date_format:  # Weekly
                current_date += timedelta(weeks=1)
            elif len(date_format) <= 7:  # Monthly
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            else:  # Daily
                current_date += timedelta(days=1)
        
        chart_data['labels'] = periods[-10:]  # Last 10 periods
        
        # Generate dataset for each assistant
        colors = [
            'rgb(255, 99, 132)', 'rgb(54, 162, 235)', 'rgb(255, 205, 86)',
            'rgb(75, 192, 192)', 'rgb(153, 102, 255)', 'rgb(255, 159, 64)'
        ]
        
        for i, assistant in enumerate(assistants[:6]):  # Top 6 assistants
            data = []
            for period in chart_data['labels']:
                # Calculate sales for this period
                if 'W' in date_format:
                    year, week = period.split('-W')
                    period_start = datetime.strptime(f'{year}-W{week}-1', '%Y-W%U-%w')
                    period_end = period_start + timedelta(weeks=1)
                elif len(date_format) <= 7:
                    year, month = period.split('-')
                    period_start = datetime(int(year), int(month), 1)
                    if int(month) == 12:
                        period_end = datetime(int(year) + 1, 1, 1)
                    else:
                        period_end = datetime(int(year), int(month) + 1, 1)
                else:
                    period_start = datetime.strptime(period, date_format)
                    period_end = period_start + timedelta(days=1)
                
                sales = Order.objects.filter(
                    shop_assistant=assistant,
                    order_date__gte=period_start,
                    order_date__lt=period_end
                ).aggregate(total=Sum('total'))['total'] or 0
                
                data.append(float(sales))
            
            chart_data['datasets'].append({
                'label': assistant.name,
                'data': data,
                'borderColor': colors[i % len(colors)],
                'backgroundColor': colors[i % len(colors)] + '20',
                'fill': False
            })
        
        return chart_data


class ShopAssistantReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/shop_assistant_reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Summary statistics
        total_assistants = ShopAssistant.objects.count()
        active_assistants = ShopAssistant.objects.filter(is_active=True).count()
        
        # Performance metrics for last 30 days
        last_30_days = timezone.now() - timedelta(days=30)
        
        # Assistant performance for last 30 days
        assistant_stats = []
        for assistant in ShopAssistant.objects.filter(is_active=True):
            orders = Order.objects.filter(
                shop_assistant=assistant,
                order_date__gte=last_30_days
            )
            
            total_sales = orders.aggregate(total_sum=Sum('total'))['total_sum'] or Decimal('0.00')
            total_orders = orders.count()
            avg_order_value = total_sales / total_orders if total_orders > 0 else Decimal('0.00')
            
            assistant_stats.append({
                'assistant': assistant,
                'total_sales': total_sales,
                'total_orders': total_orders,
                'avg_order_value': avg_order_value,
                'performance_score': (total_sales * Decimal('0.7')) + (total_orders * Decimal('0.3'))
            })
        
        # Sort by performance score
        assistant_stats.sort(key=lambda x: x['performance_score'], reverse=True)
        
        context.update({
            'total_assistants': total_assistants,
            'active_assistants': active_assistants,
            'assistant_stats': assistant_stats[:10],  # Top 10
            'report_date': timezone.now(),
        })
        
        return context