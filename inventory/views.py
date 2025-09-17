from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
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
        queryset = queryset.select_related('category', 'brand', 'supplier')
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset

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
        context['inventory'] = self.object.inventory
        return context

class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:product-list')
    permission_required = 'inventory.add_product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['root_categories'] = Category.objects.filter(parent__isnull=True)
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
        context['root_categories'] = Category.objects.filter(parent__isnull=True)
        return context

    def get_success_url(self):
        return reverse_lazy('inventory:product-detail', kwargs={'pk': self.object.pk})

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('inventory:product-list')
    permission_required = 'inventory.delete_product'

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
            
            if not reason:
                return JsonResponse({
                    'error': 'Please provide a reason for the adjustment'
                }, status=400)
            
            if adjustment == 0:
                return JsonResponse({
                    'error': 'Adjustment quantity cannot be zero'
                }, status=400)
            
            if product.inventory:
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
                    
                    # Update inventory
                    product.inventory.quantity = F('quantity') + adjustment
                    product.inventory.save()
                    product.inventory.refresh_from_db()
                    
                    return JsonResponse({
                        'success': True,
                        'new_quantity': product.inventory.quantity,
                        'message': f'Stock successfully {"increased" if adjustment > 0 else "decreased"} by {abs(adjustment)}'
                    })
                    
            return JsonResponse({
                'error': 'Product has no inventory record'
            }, status=400)
            
        except ValueError:
            return JsonResponse({
                'error': 'Invalid adjustment value'
            }, status=400)
            
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)
