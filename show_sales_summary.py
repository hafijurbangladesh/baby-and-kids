#!/usr/bin/env python
"""
Display sales data summary
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from sales.models import Order, OrderItem, Transaction

# Get summary statistics
total_orders = Order.objects.count()
total_items = OrderItem.objects.count()
total_transactions = Transaction.objects.count()

# Calculate total revenue
total_revenue = sum([order.total for order in Order.objects.all()])

print("SALES DATA GENERATION COMPLETE!")
print("=" * 60)
print("FINAL STATISTICS:")
print(f"   - Total Orders Created: {total_orders:,}")
print(f"   - Total Order Items: {total_items:,}")
print(f"   - Total Transactions: {total_transactions:,}")
print(f"   - Total Revenue Generated: TK{total_revenue:,.2f}")

# Average order value
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
print(f"   - Average Order Value: TK{avg_order_value:,.2f}")

# Sample recent orders
print(f"\nSAMPLE RECENT ORDERS:")
recent_orders = Order.objects.order_by('-id')[:5]
for order in recent_orders:
    customer_name = order.customer.name if order.customer else "Walk-in Customer"
    assistant_name = order.shop_assistant.name if order.shop_assistant else "No Assistant"
    print(f"   - Order #{order.id}: {customer_name} - TK{order.total} - Assistant: {assistant_name}")

# Date range
first_order = Order.objects.order_by('order_date').first()
last_order = Order.objects.order_by('-order_date').first()

if first_order and last_order:
    print(f"\nDATE RANGE:")
    print(f"   - First Order: {first_order.order_date.strftime('%Y-%m-%d')}")
    print(f"   - Last Order: {last_order.order_date.strftime('%Y-%m-%d')}")

# Payment method breakdown
print(f"\nPAYMENT METHODS:")
cash_count = Transaction.objects.filter(payment_method='cash').count()
card_count = Transaction.objects.filter(payment_method='card').count()
upi_count = Transaction.objects.filter(payment_method='upi').count()

print(f"   - Cash: {cash_count} transactions")
print(f"   - Card: {card_count} transactions") 
print(f"   - UPI: {upi_count} transactions")

print(f"\nSUCCESS: Your store now has 3 months of comprehensive sales data!")
print("This data can be used for analytics, reporting, and testing all features.")