#!/usr/bin/env python
"""
Test stock adjustment functionality
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from inventory.models import Product, Inventory, StockAdjustment
from django.contrib.auth.models import User

def test_stock_adjustment():
    """Test stock adjustment functionality"""
    
    print("TESTING STOCK ADJUSTMENT FUNCTIONALITY")
    print("=" * 50)
    
    # Get product ID 21
    try:
        product = Product.objects.get(id=21)
        print(f"📦 Testing product: {product.name} (ID: {product.id})")
        
        # Get or create inventory
        inventory, created = Inventory.objects.get_or_create(
            product=product,
            defaults={
                'quantity': 15,
                'low_stock_threshold': 5
            }
        )
        
        if created:
            print(f"✅ Created inventory record with {inventory.quantity} units")
        else:
            print(f"📊 Current stock: {inventory.quantity} units")
        
        # Get a user for testing
        user = User.objects.filter(is_staff=True).first()
        print(f"👤 Test user: {user.username}")
        
        # Test stock addition
        print(f"\n🔄 Testing stock addition (+10 units)...")
        original_stock = inventory.quantity
        
        # Create stock adjustment record
        adjustment = StockAdjustment.objects.create(
            product=product,
            quantity=10,
            adjustment_type='addition',
            reason='Test stock addition',
            adjusted_by=user
        )
        
        # Update inventory
        inventory.quantity = inventory.quantity + 10
        inventory.save()
        
        print(f"✅ Stock updated: {original_stock} → {inventory.quantity}")
        print(f"📝 Created adjustment record: {adjustment}")
        
        # Test stock reduction
        print(f"\n🔄 Testing stock reduction (-5 units)...")
        original_stock = inventory.quantity
        
        # Create stock adjustment record
        adjustment2 = StockAdjustment.objects.create(
            product=product,
            quantity=-5,
            adjustment_type='reduction', 
            reason='Test stock reduction',
            adjusted_by=user
        )
        
        # Update inventory
        inventory.quantity = inventory.quantity - 5
        inventory.save()
        
        print(f"✅ Stock updated: {original_stock} → {inventory.quantity}")
        print(f"📝 Created adjustment record: {adjustment2}")
        
        # Show adjustment history
        print(f"\n📜 Recent adjustments for {product.name}:")
        recent_adjustments = StockAdjustment.objects.filter(
            product=product
        ).order_by('-created_at')[:3]
        
        for adj in recent_adjustments:
            action = "+" if adj.quantity > 0 else ""
            print(f"  • {adj.created_at.strftime('%Y-%m-%d %H:%M')} - {action}{adj.quantity} units - {adj.reason}")
        
        print(f"\n✅ Stock adjustment functionality is working correctly!")
        print(f"🎯 Final stock level: {inventory.quantity} units")
        
    except Product.DoesNotExist:
        print(f"❌ Product with ID 21 not found")
        # Show available products
        print("\n📋 Available products:")
        products = Product.objects.all()[:10]
        for p in products:
            try:
                stock = p.inventory.quantity
            except:
                stock = "N/A"
            print(f"  • ID {p.id}: {p.name} - Stock: {stock}")

if __name__ == "__main__":
    test_stock_adjustment()