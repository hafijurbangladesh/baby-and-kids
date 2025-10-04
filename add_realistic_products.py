#!/usr/bin/env python
"""
Add more realistic baby and kids products to specific categories
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from inventory.models import Category, Brand, Supplier, Product, Inventory, Color, Size


def add_specific_products():
    """Add some specific, realistic baby and kids products"""
    
    # Get necessary objects
    try:
        # Baby care brands
        johnsons = Brand.objects.get(name="Johnson's")
        pampers = Brand.objects.get(name="Pampers")
        huggies = Brand.objects.get(name="Huggies")
        gerber = Brand.objects.get(name="Gerber")
        
        # Toy brands
        fisher_price = Brand.objects.get(name="Fisher-Price")
        lego = Brand.objects.get(name="Lego")
        
        # Clothing brands
        carters = Brand.objects.get(name="Carter's")
        chicco = Brand.objects.get(name="Chicco")
        
        # Suppliers
        baby_world = Supplier.objects.first()
        
        # Colors and sizes
        white = Color.objects.get_or_create(name="White")[0]
        blue = Color.objects.get_or_create(name="Blue")[0]
        pink = Color.objects.get_or_create(name="Pink")[0]
        multicolor = Color.objects.get_or_create(name="Multi-color")[0]
        
        newborn = Size.objects.get_or_create(name="Newborn")[0]
        size_6_9m = Size.objects.get_or_create(name="6-9M")[0]
        one_size = Size.objects.get_or_create(name="One Size")[0]
        
    except Exception as e:
        print(f"Error getting required data: {e}")
        return
    
    # Define specific products for baby categories
    specific_products = [
        # Johnson's products
        {
            'name': 'Johnson\'s Baby Shampoo No More Tears 500ml',
            'description': 'Gentle baby shampoo that is as mild to eyes as pure water. Clinically proven mildness formula.',
            'category_name': 'Johnson',
            'brand': johnsons,
            'price': Decimal('450.00'),
            'color': None,
            'size': one_size,
            'stock': 80
        },
        {
            'name': 'Johnson\'s Baby Oil 200ml',
            'description': 'Pure baby oil enriched with Vitamin E to keep baby\'s skin soft and smooth.',
            'category_name': 'Johnson',
            'brand': johnsons,
            'price': Decimal('320.00'),
            'color': None,
            'size': one_size,
            'stock': 65
        },
        
        # Pampers products for diaper categories
        {
            'name': 'Pampers Baby Dry Pants Size 3 (6-11kg) 58pcs',
            'description': '3 Extra Absorb Channels help distribute wetness evenly for up to 12-hour protection.',
            'category_name': 'Aloms Panty Pant',
            'brand': pampers,
            'price': Decimal('1650.00'),
            'color': white,
            'size': size_6_9m,
            'stock': 45
        },
        {
            'name': 'Huggies Dry Comfort Size 4 (7-12kg) 52pcs',
            'description': 'Double Grip Strips for better fit and 12-hour protection with 3 Extra Absorb Channels.',
            'category_name': 'Aloms Panty Pant',
            'brand': huggies,
            'price': Decimal('1780.00'),
            'color': white,
            'size': size_6_9m,
            'stock': 38
        },
        
        # Clothing items
        {
            'name': 'Carter\'s Baby Boy Cotton Bodysuit 3-Pack',
            'description': 'Soft 100% cotton bodysuits with snap closures. Machine washable.',
            'category_name': 'Boys Full Pant',
            'brand': carters,
            'price': Decimal('1200.00'),
            'color': blue,
            'size': newborn,
            'stock': 60
        },
        {
            'name': 'Carter\'s Baby Girl Romper Set',
            'description': 'Adorable romper with matching headband. Perfect for special occasions.',
            'category_name': 'Others',
            'brand': carters,
            'price': Decimal('1850.00'),
            'color': pink,
            'size': newborn,
            'stock': 35
        },
        
        # Toys and gear
        {
            'name': 'Fisher-Price Rock-a-Stack Toy',
            'description': 'Classic stacking toy helps baby develop hand-eye coordination and problem-solving skills.',
            'category_name': 'Others',
            'brand': fisher_price,
            'price': Decimal('1250.00'),
            'color': multicolor,
            'size': one_size,
            'stock': 25
        },
        {
            'name': 'LEGO DUPLO My First Number Train',
            'description': 'Colorful train teaches numbers 0-9. Perfect for toddlers 18 months and up.',
            'category_name': 'Others',
            'brand': lego,
            'price': Decimal('2850.00'),
            'color': multicolor,
            'size': one_size,
            'stock': 15
        }
    ]
    
    products_created = 0
    
    for product_data in specific_products:
        try:
            # Find category
            category = Category.objects.filter(name__icontains=product_data['category_name']).first()
            if not category:
                print(f"Category '{product_data['category_name']}' not found, skipping {product_data['name']}")
                continue
            
            # Check if product already exists
            if Product.objects.filter(name=product_data['name']).exists():
                print(f"Product '{product_data['name']}' already exists, skipping")
                continue
            
            # Create product
            product = Product.objects.create(
                name=product_data['name'],
                description=product_data['description'],
                category=category,
                brand=product_data['brand'],
                supplier=baby_world,
                price=product_data['price'],
                sku=f"REAL{Product.objects.count()+1:04d}",
                color=product_data['color'],
                size=product_data['size'],
                is_active=True
            )
            
            # Create inventory
            Inventory.objects.create(
                product=product,
                quantity=product_data['stock'],
                low_stock_threshold=5
            )
            
            products_created += 1
            print(f"✅ Created: {product.name}")
            
        except Exception as e:
            print(f"❌ Error creating {product_data['name']}: {e}")
    
    return products_created


def main():
    """Main function"""
    print("Adding realistic baby and kids products...")
    print("=" * 50)
    
    try:
        products_added = add_specific_products()
        
        print("\n" + "=" * 50)
        print(f"✅ Added {products_added} realistic products!")
        
        # Final summary
        total_products = Product.objects.count()
        total_inventory = Inventory.objects.count()
        
        print(f"\n📊 UPDATED TOTALS:")
        print(f"   • Total Products: {total_products}")
        print(f"   • Total Inventory Items: {total_inventory}")
        print(f"   • Total Brands: {Brand.objects.count()}")
        print(f"   • Total Categories: {Category.objects.count()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()