#!/usr/bin/env python
"""
Generate realistic sales data for the last 3 months
Creates orders, order items, and transactions with proper relationships
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta, time
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from sales.models import Order, OrderItem, Transaction
from inventory.models import Product, Inventory
from accounts.models import Customer, ShopAssistant


def get_random_time_in_day():
    """Get a random time during business hours (9 AM to 8 PM)"""
    hour = random.randint(9, 20)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return time(hour, minute, second)


def create_daily_orders(date, min_orders=10, max_orders=25):
    """Create orders for a specific date"""
    
    # Get available data
    customers = list(Customer.objects.all())
    shop_assistants = list(ShopAssistant.objects.all())
    users = list(User.objects.filter(is_staff=True))
    products = list(Product.objects.filter(is_active=True))
    
    if not customers or not products or not users:
        print("Missing required data (customers, products, or users)")
        return []
    
    # Determine number of orders for this day
    # Weekend might have more orders
    is_weekend = date.weekday() in [4, 5]  # Friday, Saturday
    if is_weekend:
        num_orders = random.randint(max_orders - 5, max_orders + 10)
    else:
        num_orders = random.randint(min_orders, max_orders)
    
    orders_created = []
    
    for order_num in range(num_orders):
        try:
            # Create order datetime
            order_time = get_random_time_in_day()
            order_datetime = timezone.make_aware(
                datetime.combine(date, order_time)
            )
            
            # Select customer (80% existing customers, 20% walk-in)
            customer = None
            if random.random() < 0.8 and customers:
                customer = random.choice(customers)
            
            # Select salesperson
            salesperson = random.choice(users)
            
            # Select shop assistant
            shop_assistant = None
            if shop_assistants and random.random() < 0.7:  # 70% chance
                shop_assistant = random.choice(shop_assistants)
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                salesperson=salesperson,
                shop_assistant=shop_assistant,
                order_date=order_datetime,
                status='completed'  # All historical orders are completed
            )
            
            # Add 1-5 items to the order
            num_items = random.randint(1, 5)
            order_total = Decimal('0.00')
            
            selected_products = random.sample(products, min(num_items, len(products)))
            
            for product in selected_products:
                quantity = random.randint(1, 3)
                item_price = product.price
                
                # Occasional discount (10% chance of 5-15% discount)
                if random.random() < 0.1:
                    discount_percent = random.randint(5, 15)
                    item_price = item_price * (100 - discount_percent) / 100
                    item_price = item_price.quantize(Decimal('0.01'))
                
                subtotal = item_price * quantity
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=item_price
                )
                
                order_total += subtotal
                
                # Update inventory (reduce stock)
                try:
                    inventory = product.inventory
                    if inventory.quantity >= quantity:
                        inventory.quantity -= quantity
                        inventory.save()
                except:
                    pass  # Skip inventory update if not available
            
            # Update order totals
            order.subtotal = order_total
            order.tax = (order_total * Decimal('0.10')).quantize(Decimal('0.01'))  # 10% tax
            order.total = (order.subtotal + order.tax).quantize(Decimal('0.01'))
            order.save()
            
            # Create transaction
            payment_methods = ['cash', 'card', 'upi']
            payment_method = random.choice(payment_methods)
            
            # Calculate payment details (use total with tax)
            final_total = order.total
            amount_paid = final_total
            
            # Sometimes customers pay more than exact amount (cash payments)
            if payment_method == 'cash' and random.random() < 0.3:
                # Round up to nearest 10 or 50 taka
                if final_total < 100:
                    amount_paid = ((final_total // 10) + 1) * 10
                else:
                    amount_paid = ((final_total // 50) + 1) * 50
            
            change_amount = amount_paid - final_total
            
            Transaction.objects.create(
                order=order,
                payment_method=payment_method,
                amount_paid=amount_paid,
                change_amount=change_amount,
                transaction_date=order_datetime
            )
            
            orders_created.append(order)
            
        except Exception as e:
            print(f"Error creating order {order_num + 1} for {date}: {e}")
    
    return orders_created


def generate_sales_data():
    """Generate sales data for the last 3 months"""
    
    print("Generating Sales Data for Last 3 Months...")
    print("=" * 60)
    
    # Calculate date range (last 3 months)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)
    
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Target: At least 10 orders per day")
    
    # Check available data
    customer_count = Customer.objects.count()
    product_count = Product.objects.filter(is_active=True).count()
    user_count = User.objects.filter(is_staff=True).count()
    assistant_count = ShopAssistant.objects.count()
    
    print(f"\nAvailable Data:")
    print(f"   • Customers: {customer_count}")
    print(f"   • Products: {product_count}")
    print(f"   • Staff Users: {user_count}")
    print(f"   • Shop Assistants: {assistant_count}")
    
    if product_count == 0 or user_count == 0:
        print("Error: Need products and staff users to create sales data!")
        return
    
    total_orders_created = 0
    total_days = 0
    
    # Generate data for each day
    current_date = start_date
    
    try:
        with transaction.atomic():
            while current_date <= end_date:
                # Skip future dates
                if current_date > timezone.now().date():
                    break
                
                daily_orders = create_daily_orders(current_date)
                total_orders_created += len(daily_orders)
                total_days += 1
                
                if len(daily_orders) > 0:
                    print(f"{current_date}: Created {len(daily_orders)} orders")
                
                current_date += timedelta(days=1)
            
            print(f"\nSales Data Generation Complete!")
            print("=" * 60)
            
            # Final statistics
            print(f"SUMMARY:")
            print(f"   • Total Days: {total_days}")
            print(f"   • Total Orders: {total_orders_created}")
            print(f"   • Average Orders per Day: {total_orders_created / total_days if total_days > 0 else 0:.1f}")
            
            # Database totals
            total_db_orders = Order.objects.count()
            total_db_items = OrderItem.objects.count()
            total_db_transactions = Transaction.objects.count()
            total_revenue = sum([order.total for order in Order.objects.all()])
            
            print(f"\nDATABASE TOTALS:")
            print(f"   • Total Orders: {total_db_orders}")
            print(f"   • Total Order Items: {total_db_items}")
            print(f"   • Total Transactions: {total_db_transactions}")
            print(f"   • Total Revenue: TK{total_revenue:,.2f}")
            
            # Recent orders sample
            recent_orders = Order.objects.order_by('-order_date')[:3]
            print(f"\nSAMPLE RECENT ORDERS:")
            for order in recent_orders:
                customer_name = order.customer.name if order.customer else "Walk-in"
                assistant_name = order.shop_assistant.name if order.shop_assistant else "N/A"
                print(f"   • Order #{order.id}: {customer_name} - TK{order.total} - Assistant: {assistant_name}")
    
    except Exception as e:
        print(f"Error generating sales data: {e}")
        raise


def main():
    """Main function"""
    print("Baby & Kids Store - Sales Data Generator")
    print("Generating realistic sales data for performance testing...")
    print()
    
    try:
        generate_sales_data()
        print(f"\nAll sales data generated successfully!")
        print("Your store now has comprehensive sales history for analytics and reporting.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()