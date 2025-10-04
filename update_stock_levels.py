#!/usr/bin/env python
"""
Update stock levels for all products to ensure minimum stock of 10 items
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from inventory.models import Product, Inventory
from django.db import models


def update_stock_levels():
    """Update all product stock levels to minimum of 10"""
    
    print("Updating Product Stock Levels...")
    print("=" * 50)
    
    # Get all products and their inventory
    products_updated = 0
    total_products = Product.objects.count()
    
    print(f"Checking {total_products} products...")
    
    for product in Product.objects.all():
        try:
            # Get or create inventory for this product
            inventory, created = Inventory.objects.get_or_create(
                product=product,
                defaults={
                    'quantity': 15,  # Default to 15 if creating new
                    'low_stock_threshold': 5
                }
            )
            
            # Check if stock is below 10
            if inventory.quantity < 10:
                old_quantity = inventory.quantity
                inventory.quantity = 15  # Set to 15 for better buffer
                inventory.save()
                
                print(f"Updated {product.name}: {old_quantity} → {inventory.quantity}")
                products_updated += 1
            else:
                print(f"OK: {product.name} - Current stock: {inventory.quantity}")
                
        except Exception as e:
            print(f"Error updating {product.name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"Stock Update Complete!")
    print(f"✅ Products Updated: {products_updated}")
    print(f"✅ Products Already OK: {total_products - products_updated}")
    
    # Show summary statistics
    low_stock_count = Inventory.objects.filter(quantity__lt=10).count()
    avg_stock = Inventory.objects.aggregate(avg_stock=models.Avg('quantity'))['avg_stock'] or 0
    
    print(f"\nFinal Stock Status:")
    print(f"• Products with stock < 10: {low_stock_count}")
    print(f"• Average stock level: {avg_stock:.1f}")
    print(f"• Total inventory items: {Inventory.objects.count()}")


def show_stock_summary():
    """Show current stock summary"""
    
    print("\nCurrent Stock Summary:")
    print("-" * 30)
    
    # Stock level categories
    very_low = Inventory.objects.filter(quantity__lt=5).count()
    low = Inventory.objects.filter(quantity__gte=5, quantity__lt=10).count() 
    good = Inventory.objects.filter(quantity__gte=10, quantity__lt=20).count()
    high = Inventory.objects.filter(quantity__gte=20).count()
    
    print(f"Very Low (< 5):    {very_low} products")
    print(f"Low (5-9):         {low} products")
    print(f"Good (10-19):      {good} products")
    print(f"High (20+):        {high} products")
    
    # Top 5 products by stock
    print(f"\nTop 5 Products by Stock:")
    top_stock = Inventory.objects.select_related('product').order_by('-quantity')[:5]
    for inv in top_stock:
        print(f"• {inv.product.name}: {inv.quantity} units")
    
    # Products that might need attention
    print(f"\nProducts Below 10 Units:")
    low_stock = Inventory.objects.select_related('product').filter(quantity__lt=10).order_by('quantity')
    if low_stock.exists():
        for inv in low_stock:
            print(f"• {inv.product.name}: {inv.quantity} units")
    else:
        print("✅ All products have adequate stock!")


def main():
    """Main function"""
    print("🏪 Baby & Kids Store - Stock Level Updater")
    print("Ensuring all products have minimum stock of 10 units...")
    print()
    
    try:
        # Update stock levels
        update_stock_levels()
        
        # Show summary
        show_stock_summary()
        
        print(f"\n✅ Stock update completed successfully!")
        print("All products now have adequate inventory levels for sales operations.")
        
    except Exception as e:
        print(f"❌ Error updating stock levels: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()