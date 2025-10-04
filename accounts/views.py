from datetime import datetime
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, ProtectedError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView, DetailView, CreateView, 
    UpdateView, DeleteView, TemplateView
)

from .models import Customer, UserProfile, ShopAssistant
from .forms import CustomerForm, UserProfileForm

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'accounts/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related()
        
        # Get search parameters
        search_query = self.request.GET.get('search', '').strip()
        phone_query = self.request.GET.get('phone', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()

        # Search by name or email
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Search by phone number
        if phone_query:
            # Remove any formatting from the search query
            phone_cleaned = ''.join(filter(str.isdigit, phone_query))
            queryset = queryset.filter(phone_number__icontains=phone_cleaned)
        
        # Search by last purchase date range
        try:
            # Get all customers with orders in the date range
            orders_query = Q()
            if date_from:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                orders_query &= Q(order__order_date__gte=date_from)
            
            if date_to:
                date_to = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
                orders_query &= Q(order__order_date__lte=date_to)
            
            if date_from or date_to:
                # Filter customers who have orders in the specified date range
                queryset = queryset.filter(orders_query).distinct()
        except ValueError:
            # If date parsing fails, ignore the date filter
            pass

        return queryset.order_by('-updated_at')

@login_required
def customer_search(request):
    query = request.GET.get('q', '').strip()
    date_query = request.GET.get('date', '').strip()
    page = int(request.GET.get('page', 1))
    per_page = 10

    # Start with all customers
    customers = Customer.objects.all()
    
    if query:
        # Search in name, email, and phone number
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query)
        )
    
    if date_query:
        try:
            search_date = datetime.strptime(date_query, '%Y-%m-%d').date()
            # Search for orders on the specified date
            customers = customers.filter(
                order__order_date__date=search_date
            ).distinct()
        except ValueError:
            pass
    
    # Apply pagination after all filters
    customers = customers.order_by('-updated_at')[(page - 1) * per_page:page * per_page]
    
    items = [{
        'id': customer.id,
        'name': customer.name,
        'phone': customer.phone_number or '',
        'email': customer.email or ''
    } for customer in customers]
    
    # Add "Add New Customer" option as the first item if there's a query
    if query:
        items.insert(0, {
            'id': 'new',
            'name': f'Add New Customer: {query}',
            'phone': '',
            'email': ''
        })
    
    return JsonResponse({
        'items': items,
        'has_more': customers.count() >= per_page
    })

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('accounts:customer-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.object:  # If this is a new customer
            context['order_count'] = 0
            context['total_purchase_value'] = 0
            context['recent_orders'] = []
        return context

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:  # If this is an existing customer
            context['order_count'] = self.object.order_set.count()
            context['total_purchase_value'] = self.object.total_purchase_value
            context['recent_orders'] = self.object.order_set.all()[:5]
        return context

    def get_success_url(self):
        return reverse_lazy('accounts:customer-detail', kwargs={'pk': self.object.pk})

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'accounts/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent orders and last order date
        orders = self.object.order_set.select_related('salesperson')
        context['orders'] = orders
        context['last_order_date'] = orders.order_by('-order_date').values_list('order_date', flat=True).first()
        return context

@login_required
@require_http_methods(["POST"])
def customer_create(request):
    try:
        data = json.loads(request.body)
        customer = Customer.objects.create(
            name=data['name'],
            phone=data['phone'],
            email=data.get('email', '')
        )
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user.userprofile

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('accounts:customer-list')
    
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                "This customer cannot be deleted because they have orders in the system. "
                "Please delete all associated orders first if you really need to remove this customer."
            )
            return redirect('accounts:customer-detail', pk=kwargs['pk'])

class SalespersonListView(LoginRequiredMixin, ListView):
    model = UserProfile
    template_name = 'accounts/salesperson_list.html'
    context_object_name = 'salespersons'
    paginate_by = 10

    def get_queryset(self):
        return UserProfile.objects.filter(
            is_salesperson=True
        ).select_related('user').order_by('user__first_name', 'user__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add sales statistics for each salesperson
        from sales.models import Order
        from django.db.models import Sum, Count
        from decimal import Decimal
        
        for profile in context['salespersons']:
            stats = Order.objects.filter(
                salesperson=profile.user,
                status='completed'
            ).aggregate(
                total_sales=Sum('total'),
                total_orders=Count('id')
            )
            profile.total_sales = stats['total_sales'] or Decimal('0.00')
            profile.total_orders = stats['total_orders'] or 0
        
        return context

# Shop Assistant Views
class ShopAssistantListView(LoginRequiredMixin, ListView):
    model = ShopAssistant
    template_name = 'accounts/shop_assistant_list.html'
    context_object_name = 'shop_assistants'
    paginate_by = 10

    def get_queryset(self):
        queryset = ShopAssistant.objects.all().order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(contact_number__icontains=search_query)
            )
        
        # Filter by active status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        
        # Add performance statistics for each assistant
        for assistant in context['shop_assistants']:
            assistant.cached_total_sales = assistant.total_sales
            assistant.cached_total_orders = assistant.total_orders
        
        return context

class ShopAssistantDetailView(LoginRequiredMixin, DetailView):
    model = ShopAssistant
    template_name = 'accounts/shop_assistant_detail.html'
    context_object_name = 'shop_assistant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assistant = self.object
        
        # Get recent orders
        from sales.models import Order
        context['recent_orders'] = Order.objects.filter(
            shop_assistant=assistant,
            status='completed'
        ).select_related('customer').order_by('-order_date')[:10]
        
        # Get performance statistics for different periods
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        context['today_performance'] = assistant.get_performance_data(today, today)
        context['week_performance'] = assistant.get_performance_data(week_ago, today)
        context['month_performance'] = assistant.get_performance_data(month_ago, today)
        context['overall_performance'] = assistant.get_performance_data()
        
        return context

class ShopAssistantCreateView(LoginRequiredMixin, CreateView):
    model = ShopAssistant
    template_name = 'accounts/shop_assistant_form.html'
    fields = ['name', 'contact_number', 'joining_date', 'is_active', 'address', 'notes']
    
    def get_success_url(self):
        messages.success(self.request, f'Shop assistant "{self.object.name}" has been created successfully.')
        return reverse_lazy('accounts:shop-assistant-detail', kwargs={'pk': self.object.pk})

class ShopAssistantUpdateView(LoginRequiredMixin, UpdateView):
    model = ShopAssistant
    template_name = 'accounts/shop_assistant_form.html'
    fields = ['name', 'contact_number', 'joining_date', 'is_active', 'address', 'notes']
    
    def get_success_url(self):
        messages.success(self.request, f'Shop assistant "{self.object.name}" has been updated successfully.')
        return reverse_lazy('accounts:shop-assistant-detail', kwargs={'pk': self.object.pk})

class ShopAssistantDeleteView(LoginRequiredMixin, DeleteView):
    model = ShopAssistant
    template_name = 'accounts/shop_assistant_confirm_delete.html'
    context_object_name = 'shop_assistant'
    success_url = reverse_lazy('accounts:shop-assistant-list')
    
    def delete(self, request, *args, **kwargs):
        assistant_name = self.get_object().name
        messages.success(self.request, f'Shop assistant "{assistant_name}" has been deleted successfully.')
        return super().delete(request, *args, **kwargs)

@login_required
def shop_assistant_search(request):
    """API endpoint for searching shop assistants (for POS integration)"""
    query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    per_page = 10

    assistants = ShopAssistant.objects.filter(is_active=True)
    
    if query:
        assistants = assistants.filter(
            Q(name__icontains=query) |
            Q(assigned_shop__icontains=query)
        )
    
    assistants = assistants.order_by('name')[(page - 1) * per_page:page * per_page]
    
    items = [{
        'id': assistant.id,
        'name': assistant.name,
        'shop': assistant.assigned_shop,
        'display_text': f"{assistant.name} ({assistant.assigned_shop})"
    } for assistant in assistants]
    
    return JsonResponse({
        'items': items,
        'has_more': assistants.count() >= per_page
    })
