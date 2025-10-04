from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db.models import F
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Product, Inventory, StockAdjustment, Category
from .forms import ProductForm

@login_required
def get_subcategories(request):
    parent_id = request.GET.get('parent_id')
    if parent_id:
        subcategories = Category.objects.filter(parent_id=parent_id).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    else:
        categories = Category.objects.filter(parent__isnull=True).values('id', 'name')
        return JsonResponse(list(categories), safe=False)

@login_required
def get_category_chain(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    chain = []
    current = category
    
    # Build the chain from current category up to root
    while current:
        chain.append({'id': current.id, 'name': current.name})
        current = current.parent
    
    # Reverse to get root->leaf order
    chain.reverse()
    return JsonResponse(chain, safe=False)

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('category', 'brand', 'supplier', 'inventory')
        queryset = queryset.filter(is_active=True)
        search_query = self.request.GET.get('search')
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(sku__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(brand__name__icontains=search_query)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure all products have inventory records
        for product in context['products']:
            Inventory.objects.get_or_create(
                product=product,
                defaults={
                    'quantity': 0,
                    'low_stock_threshold': 5
                }
            )
        return context

@login_required
def product_search(request):
    query = request.GET.get('q', '')
    page = int(request.GET.get('page', 1))
    per_page = 10
    
    products = Product.objects.select_related('inventory').filter(
        name__icontains=query
    )[(page - 1) * per_page:page * per_page]
    
    items = [{
        'id': product.id,
        'name': product.name,
        'price': float(product.selling_price),
        'stock': product.inventory.current_stock,
        'image': product.image.url if product.image else None,
        'description': str(product.description)
    } for product in products]
    
    return JsonResponse({
        'items': items,
        'has_more': products.count() >= per_page
    })

@login_required
def recent_products(request):
    products = Product.objects.select_related('inventory').order_by('-created_at')[:12]
    
    items = [{
        'id': product.id,
        'name': product.name,
        'price': float(product.selling_price),
        'stock': product.inventory.current_stock,
        'image': product.image.url if product.image else None,
        'description': str(product.description)
    } for product in products]
    
    return JsonResponse({
        'products': items
    })

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'inventory/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Create inventory if it doesn't exist
        inventory, created = Inventory.objects.get_or_create(
            product=self.object,
            defaults={
                'quantity': 0,
                'low_stock_threshold': 5
            }
        )
        context['inventory'] = inventory
        return context

class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:product-list')
    permission_required = 'inventory.add_product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all categories ordered by their hierarchy
        categories = Category.objects.all().order_by('parent__id', 'name')
        # Convert to list of {id, name, hierarchy} for the template
        context['categories'] = [
            {'id': cat.id, 'name': cat.name, 'hierarchy': cat.get_hierarchy()}
            for cat in categories
        ]
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create corresponding inventory record
        Inventory.objects.create(
            product=self.object,
            quantity=0,
            low_stock_threshold=5  # Default value
        )
        return response

class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    permission_required = 'inventory.change_product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all categories ordered by their hierarchy
        categories = Category.objects.all().order_by('parent__id', 'name')
        # Convert to list of {id, name, hierarchy} for the template
        context['categories'] = [
            {'id': cat.id, 'name': cat.name, 'hierarchy': cat.get_hierarchy()}
            for cat in categories
        ]
        return context

    def get_success_url(self):
        return reverse_lazy('inventory:product-detail', kwargs={'pk': self.object.pk})

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('inventory:product-list')
    permission_required = 'inventory.delete_product'
    
    def post(self, request, *args, **kwargs):
        """
        Override post to handle the deactivation instead of deletion
        """
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        
        from django.contrib import messages
        messages.success(self.request, f'Product "{self.object.name}" has been deactivated.')
        
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

class LowStockListView(LoginRequiredMixin, ListView):
    model = Inventory
    template_name = 'inventory/low_stock_list.html'
    context_object_name = 'low_stock_items'

    def get_queryset(self):
        return Inventory.objects.filter(
            quantity__lte=F('low_stock_threshold')
        ).select_related('product')


@login_required
def update_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            adjustment = int(request.POST.get('adjustment', 0))
            reason = request.POST.get('reason', '').strip()
            
            # Validation
            if not reason:
                from django.contrib import messages
                messages.error(request, 'Please provide a reason for the adjustment.')
                return HttpResponseRedirect(reverse('inventory:product-detail', kwargs={'pk': pk}))
            
            if adjustment == 0:
                from django.contrib import messages
                messages.error(request, 'Adjustment quantity cannot be zero.')
                return HttpResponseRedirect(reverse('inventory:product-detail', kwargs={'pk': pk}))
            
            # Get or create inventory if it doesn't exist
            inventory, created = Inventory.objects.get_or_create(
                product=product,
                defaults={
                    'quantity': 0,
                    'low_stock_threshold': 5
                }
            )
            
            # Check if adjustment would result in negative stock
            new_quantity = inventory.quantity + adjustment
            if new_quantity < 0:
                from django.contrib import messages
                messages.error(request, f'Adjustment would result in negative stock. Current stock: {inventory.quantity}')
                return HttpResponseRedirect(reverse('inventory:product-detail', kwargs={'pk': pk}))
            
            with transaction.atomic():
                # Determine adjustment type
                if adjustment > 0:
                    adjustment_type = 'addition'
                elif adjustment < 0:
                    adjustment_type = 'reduction'
                else:
                    adjustment_type = 'correction'
                
                # Create stock adjustment record
                StockAdjustment.objects.create(
                    product=product,
                    quantity=adjustment,
                    adjustment_type=adjustment_type,
                    reason=reason,
                    adjusted_by=request.user
                )
                
                # Update inventory quantity
                inventory.quantity = new_quantity
                inventory.save()
                
                from django.contrib import messages
                action = "increased" if adjustment > 0 else "decreased"
                messages.success(request, f'Stock successfully {action} by {abs(adjustment)} units. New stock: {inventory.quantity}')
                
            # Redirect back to product detail page
            return HttpResponseRedirect(reverse('inventory:product-detail', kwargs={'pk': pk}))
                
        except ValueError:
            from django.contrib import messages
            messages.error(request, 'Invalid adjustment value. Please enter a valid number.')
            return HttpResponseRedirect(reverse('inventory:product-detail', kwargs={'pk': pk}))
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'An error occurred while updating stock: {str(e)}')
            return HttpResponseRedirect(reverse('inventory:product-detail', kwargs={'pk': pk}))
    
    # If not POST request, redirect to product detail
    return HttpResponseRedirect(reverse('inventory:product-detail', kwargs={'pk': pk}))


class InventoryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'reports/inventory_report.html'
    permission_required = 'inventory.view_inventory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all products with their inventory
        products = Product.objects.select_related(
            'inventory', 'category', 'brand', 'supplier'
        ).filter(is_active=True)

        # Get low stock products
        low_stock = products.filter(
            inventory__quantity__lte=F('inventory__low_stock_threshold'),
            inventory__quantity__gt=0
        )

        # Get out of stock products
        out_of_stock = products.filter(inventory__quantity=0)

        # Calculate category totals
        from django.db.models import Sum
        category_totals = Product.objects.values(
            'category__name'
        ).annotate(
            total_items=Sum('inventory__quantity'),
            total_value=Sum(F('inventory__quantity') * F('price'))
        ).filter(is_active=True)

        context.update({
            'products': products,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'category_totals': category_totals,
        })

        return context
