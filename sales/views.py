from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.http import JsonResponse, HttpResponseRedirect
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse
from .models import Order, OrderItem, Transaction
from inventory.models import Product, Inventory, Category, Brand
from accounts.models import Customer
import json
import decimal

@login_required
def get_product_info(request, product_id):
    product = get_object_or_404(Product.objects.select_related('inventory'), pk=product_id)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'price': str(product.price),
        'stock': product.inventory.quantity
    })

class SaleListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'sales/sale_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-order_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('customer', 'salesperson')

        # Apply filters if provided
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')

        if start_date:
            queryset = queryset.filter(order_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__date__lte=end_date)
        if status:
            queryset = queryset.filter(status=status)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_status_choices'] = Order.ORDER_STATUS_CHOICES
        return context

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'sales/order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.orderitem_set.select_related('product')
        context['transaction'] = self.object.transaction
        return context

class POSView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'sales/pos.html'

    def test_func(self):
        return self.request.user.userprofile.is_salesperson

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.select_related('inventory', 'category', 'brand')
        context['customers'] = Customer.objects.all()
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        return context

@login_required
def complete_sale(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        total_amount = decimal.Decimal('0.00')
        
        with transaction.atomic():
            # First, create the order with initial values
            order = Order(
                salesperson=request.user,
                status='pending',
                subtotal=decimal.Decimal('0.00'),
                tax=decimal.Decimal('0.00'),
                total=decimal.Decimal('0.00')
            )
            
            # Add customer if provided
            if data.get('customer'):
                try:
                    customer = Customer.objects.get(pk=data['customer'])
                    order.customer = customer
                except Customer.DoesNotExist:
                    # Customer ID invalid - continue as walk-in customer
                    pass
            
            # Save order to get the ID
            order.save()
            
            # Create order items
            for item in data['items']:
                product = get_object_or_404(Product, pk=item['id'])
                inventory = product.inventory
                quantity = int(item['quantity'])
                
                # Check stock availability
                if inventory.quantity < quantity:
                    raise ValueError(f'Insufficient stock for {product.name}')
                
                # Calculate item total
                price = decimal.Decimal(str(item['price']))
                item_total = price * quantity
                total_amount += item_total
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                
                # Update inventory
                inventory.quantity = F('quantity') - quantity
                inventory.save()
                
                # Check if stock is below threshold after update
                inventory.refresh_from_db()
                if inventory.quantity <= inventory.low_stock_threshold:
                    # TODO: Implement low stock notification system
                    pass
            
            # Add tax
            tax_amount = total_amount * decimal.Decimal('0.10')  # 10% tax
            total_with_tax = total_amount + tax_amount
            
            # Validate payment amount
            amount_paid = decimal.Decimal(str(data['amount_paid']))
            if amount_paid < total_with_tax:
                raise ValueError('Insufficient payment amount')
            
            # Create transaction
            Transaction.objects.create(
                order=order,
                payment_method=data['payment_method'],
                amount_paid=amount_paid,
                change_amount=amount_paid - total_with_tax
            )
            
            # Update order totals and status
            order.subtotal = total_amount
            order.tax = tax_amount
            order.total = total_with_tax
            order.status = 'completed'  # Set status to completed after successful payment
            order.save()

            # Double-check all values are properly saved with a small tolerance for floating-point precision
            order.refresh_from_db()
            
            # Check if the difference is more than 0.01 (1 cent)
            if abs(order.total - total_with_tax) > decimal.Decimal('0.01'):
                raise ValueError(f'Order total mismatch (Expected: {total_with_tax}, Got: {order.total}) - please try again')
            
            # Update customer's total purchase value
            if order.customer:
                order.customer.update_total_purchase_value()
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'redirect_url': f'/sales/order/{order.id}/'
            })
        
    except (ValueError, decimal.InvalidOperation) as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred while processing the sale'
        }, status=500)

@login_required
def get_product_info(request, pk):
    product = get_object_or_404(Product.objects.select_related('inventory'), pk=pk)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'price': str(product.price),
        'stock': product.inventory.quantity
    })

@login_required
def email_receipt(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Render the receipt template
            html_content = render_to_string('sales/email/receipt.html', {
                'order': order,
                'items': order.orderitem_set.select_related('product'),
            })
            
            # Send email
            try:
                send_mail(
                    subject=f'Receipt for Order #{order.id}',
                    message='Please see the attached receipt.',
                    from_email=None,  # Use DEFAULT_FROM_EMAIL from settings
                    recipient_list=[email],
                    html_message=html_content,
                )
                messages.success(request, 'Receipt has been sent successfully!')
            except Exception as e:
                messages.error(request, 'Failed to send receipt. Please try again.')
        else:
            messages.error(request, 'Please provide an email address.')
    
    return redirect('sales:order-detail', pk=order.pk)

@login_required
def process_refund(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        items = request.POST.getlist('items[]')
        reason = request.POST.get('reason')
        
        if not items:
            messages.error(request, 'Please select at least one item to return.')
            return redirect('sales:order-detail', pk=order.pk)
        
        try:
            with transaction.atomic():
                # Process returns and update inventory
                for item_id in items:
                    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
                    
                    # Update inventory
                    inventory = order_item.product.inventory
                    inventory.quantity = F('quantity') + order_item.quantity
                    inventory.save()
                    
                    # Mark item as returned
                    order_item.status = 'returned'
                    order_item.save()
                
                # Update customer's total purchase value after refund
                if order.customer:
                    order.customer.update_total_purchase_value()
                
                # You might want to create a Refund model to track refunds
                # Refund.objects.create(
                #     order=order,
                #     amount=refund_amount,
                #     reason=reason,
                #     processed_by=request.user
                # )
                
                messages.success(request, 'Return processed successfully.')
        except Exception as e:
            messages.error(request, 'Failed to process return. Please try again.')
    
    return redirect('sales:order-detail', pk=order.pk)

@login_required
@transaction.atomic
def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        items = data.get('items', [])
        payment_method = data.get('payment_method')

        if not items:
            return JsonResponse({'error': 'No items in order'}, status=400)

        # Create order
        customer = get_object_or_404(Customer, pk=customer_id)
        order = Order.objects.create(
            customer=customer,
            salesperson=request.user,
            status='completed'
        )

        total_amount = 0
        # Process items
        for item in items:
            product = get_object_or_404(Product, pk=item['product_id'])
            quantity = int(item['quantity'])
            
            # Check stock
            inventory = product.inventory
            if inventory.quantity < quantity:
                transaction.set_rollback(True)
                return JsonResponse({
                    'error': f'Insufficient stock for {product.name}'
                }, status=400)
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
            
            # Update inventory
            inventory.quantity = F('quantity') - quantity
            inventory.save()
            
            total_amount += product.price * quantity

        # Update order total
        order.total_price = total_amount
        order.save()

        # Create transaction
        Transaction.objects.create(
            order=order,
            payment_method=payment_method,
            amount_paid=total_amount
        )

        # Update customer's total purchase value
        customer.total_purchase_value = F('total_purchase_value') + total_amount
        customer.save()

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'total_amount': str(total_amount)
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
