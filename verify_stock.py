#!/usr/bin/env python
"""
Verify stock levels after update
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from inventory.models import Product, Inventory

print("STOCK VERIFICATION REPORT")
print("=" * 50)

# Get sample products to verify
sample_products = Product.objects.all()[:10]
print("Sample Product Stock Levels:")
print("-" * 40)

for product in sample_products:
    try:
        inv = product.inventory
        print(f"{product.name[:35]:<35} : {inv.quantity} units")
    except Inventory.DoesNotExist:
        print(f"{product.name[:35]:<35} : No inventory!")

# Summary statistics
total_products = Product.objects.count()
total_inventory = Inventory.objects.count()
products_with_min_stock = Inventory.objects.filter(quantity__gte=10).count()
products_low_stock = Inventory.objects.filter(quantity__lt=10).count()

print(f"\nSUMMARY:")
print("-" * 20)
print(f"Total Products:           {total_products}")
print(f"Total Inventory Records:  {total_inventory}")
print(f"Products with >= 10 stock: {products_with_min_stock}")
print(f"Products with < 10 stock:  {products_low_stock}")

if products_low_stock == 0:
    print("\n✅ SUCCESS: All products have at least 10 units in stock!")
else:
    print(f"\n⚠️  WARNING: {products_low_stock} products still have low stock!")

# Show realistic products specifically
print(f"\nREALISTIC PRODUCTS STOCK:")
print("-" * 30)
realistic_products = Product.objects.filter(sku__startswith='REAL')
for product in realistic_products:
    try:
        inv = product.inventory  
        print(f"• {product.name[:40]:<40} : {inv.quantity} units")
    except Inventory.DoesNotExist:
        print(f"• {product.name[:40]:<40} : No inventory!")
        
print(f"\n🎉 Stock update verification complete!")