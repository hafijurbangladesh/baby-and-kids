#!/usr/bin/env python
"""
Sample Data Creation Script for Baby and Kids Store
This script creates comprehensive sample data for testing the store management system.
"""

import os
import sys
import django
from decimal import Decimal
from django.db import transaction

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from inventory.models import Category, Brand, Supplier, Product, Inventory, Color, Size
from accounts.models import Customer


def create_brands():
    """Create sample brands for baby and kids products"""
    brands_data = [
        'Carter\'s',
        'Fisher-Price', 
        'Pampers',
        'Johnson\'s',
        'Gerber',
        'Huggies',
        'Chicco',
        'Lego',
    ]
    
    brands = []
    for brand_name in brands_data:
        brand, created = Brand.objects.get_or_create(name=brand_name)
        brands.append(brand)
        if created:
            print(f"Created brand: {brand.name}")
    
    return brands


def create_suppliers():
    """Create sample suppliers"""
    suppliers_data = [
        {'name': 'Baby World Wholesale', 'contact_person': 'Rahman Khan', 'contact_info': 'Phone: 01712345678, Email: info@babyworldbd.com, Address: Dhanmondi, Dhaka'},
        {'name': 'Kids Paradise Ltd', 'contact_person': 'Fatima Ahmed', 'contact_info': 'Phone: 01787654321, Email: sales@kidsparadise.com, Address: Gulshan, Dhaka'},
        {'name': 'Toy Kingdom', 'contact_person': 'Karim Hossain', 'contact_info': 'Phone: 01598765432, Email: orders@toykingdom.bd, Address: Uttara, Dhaka'},
        {'name': 'Baby Care Distributors', 'contact_person': 'Nasreen Begum', 'contact_info': 'Phone: 01634567890, Email: contact@babycarebd.com, Address: Mirpur, Dhaka'},
    ]
    
    suppliers = []
    for supplier_data in suppliers_data:
        supplier, created = Supplier.objects.get_or_create(
            name=supplier_data['name'],
            defaults=supplier_data
        )
        suppliers.append(supplier)
        if created:
            print(f"Created supplier: {supplier.name}")
    
    return suppliers


def create_colors_sizes():
    """Create color and size options"""
    colors_data = [
        'Red', 'Blue', 'Pink', 'Yellow', 'Green', 'White', 'Black', 
        'Purple', 'Orange', 'Multi-color', 'Beige', 'Navy Blue'
    ]
    
    sizes_data = [
        'Newborn', '0-3M', '3-6M', '6-9M', '9-12M', '12-18M', '18-24M',
        '2T', '3T', '4T', '5T', 'XS', 'S', 'M', 'L', 'XL', 'One Size'
    ]
    
    colors = []
    for color_name in colors_data:
        color, created = Color.objects.get_or_create(name=color_name)
        colors.append(color)
        if created:
            print(f"Created color: {color.name}")
    
    sizes = []
    for size_name in sizes_data:
        size, created = Size.objects.get_or_create(name=size_name)
        sizes.append(size)
        if created:
            print(f"Created size: {size.name}")
    
    return colors, sizes


def create_sample_products():
    """Create sample products for each category"""
    
    # Get existing data
    categories = list(Category.objects.all())
    brands = list(Brand.objects.all())
    suppliers = list(Supplier.objects.all())
    colors, sizes = create_colors_sizes()
    
    if not categories:
        print("No categories found! Please create categories first.")
        return
    
    # Sample products data organized by category keywords
    products_by_category = {
        'clothing': [
            {
                'name': 'Cotton Onesie Set',
                'description': 'Soft cotton onesie set for babies, pack of 3',
                'brand_keyword': 'Carter\'s',
                'price': Decimal('1200.00'),
                'colors': ['White', 'Pink', 'Blue'],
                'sizes': ['Newborn', '0-3M', '3-6M']
            },
            {
                'name': 'Kids T-Shirt',
                'description': 'Comfortable cotton t-shirt for kids',
                'brand_keyword': 'Carter\'s',
                'price': Decimal('850.00'),
                'colors': ['Red', 'Blue', 'Yellow'],
                'sizes': ['2T', '3T', '4T', '5T']
            },
        ],
        'toys': [
            {
                'name': 'Educational Building Blocks',
                'description': 'Colorful building blocks for cognitive development',
                'brand_keyword': 'Fisher-Price',
                'price': Decimal('2500.00'),
                'colors': ['Multi-color'],
                'sizes': ['One Size']
            },
            {
                'name': 'LEGO Classic Set',
                'description': 'Creative building set with 484 pieces',
                'brand_keyword': 'Lego',
                'price': Decimal('4500.00'),
                'colors': ['Multi-color'],
                'sizes': ['One Size']
            },
        ],
        'diaper': [
            {
                'name': 'Premium Diapers',
                'description': '12-hour protection diapers, pack of 60',
                'brand_keyword': 'Pampers',
                'price': Decimal('1800.00'),
                'colors': ['White'],
                'sizes': ['Newborn', '0-3M', '3-6M', '6-9M']
            },
            {
                'name': 'Overnight Diapers',
                'description': 'Extra protection for overnight use, pack of 48',
                'brand_keyword': 'Huggies',
                'price': Decimal('2200.00'),
                'colors': ['White'],
                'sizes': ['6-9M', '9-12M', '12-18M']
            },
        ],
        'food': [
            {
                'name': 'Organic Baby Cereal',
                'description': 'Iron-fortified rice cereal for babies',
                'brand_keyword': 'Gerber',
                'price': Decimal('650.00'),
                'colors': ['Beige'],
                'sizes': ['One Size']
            },
            {
                'name': 'Baby Fruit Puree',
                'description': 'Organic apple and banana puree, pack of 6',
                'brand_keyword': 'Gerber',
                'price': Decimal('950.00'),
                'colors': ['Multi-color'],
                'sizes': ['One Size']
            },
        ],
        'care': [
            {
                'name': 'Baby Shampoo',
                'description': 'Gentle, tear-free baby shampoo 500ml',
                'brand_keyword': 'Johnson\'s',
                'price': Decimal('420.00'),
                'colors': ['Yellow'],
                'sizes': ['One Size']
            },
            {
                'name': 'Baby Lotion',
                'description': 'Moisturizing baby lotion 400ml',
                'brand_keyword': 'Johnson\'s',
                'price': Decimal('480.00'),
                'colors': ['White'],
                'sizes': ['One Size']
            },
        ],
        'gear': [
            {
                'name': 'Baby Stroller',
                'description': 'Lightweight, foldable baby stroller',
                'brand_keyword': 'Chicco',
                'price': Decimal('15000.00'),
                'colors': ['Black', 'Navy Blue'],
                'sizes': ['One Size']
            },
            {
                'name': 'Baby Car Seat',
                'description': 'Safety-certified infant car seat',
                'brand_keyword': 'Chicco',
                'price': Decimal('18000.00'),
                'colors': ['Black', 'Red'],
                'sizes': ['One Size']
            },
        ],
        'shoes': [
            {
                'name': 'Baby Soft Shoes',
                'description': 'Soft sole shoes for first walkers',
                'brand_keyword': 'Carter\'s',
                'price': Decimal('1200.00'),
                'colors': ['Pink', 'Blue', 'White'],
                'sizes': ['0-3M', '3-6M', '6-9M']
            },
            {
                'name': 'Kids Sneakers',
                'description': 'Comfortable sneakers for active kids',
                'brand_keyword': 'Carter\'s',
                'price': Decimal('2200.00'),
                'colors': ['Red', 'Blue', 'Black'],
                'sizes': ['2T', '3T', '4T', '5T']
            },
        ]
    }
    
    # Create products for each category
    created_products = []
    
    for category in categories:
        category_name_lower = category.name.lower()
        
        # Find matching products for this category
        matching_products = []
        for keyword, products in products_by_category.items():
            if keyword in category_name_lower or any(word in category_name_lower for word in keyword.split()):
                matching_products.extend(products)
        
        # If no specific match, use general products
        if not matching_products:
            # Create generic products for this category
            matching_products = [
                {
                    'name': f'{category.name} Item 1',
                    'description': f'Quality {category.name.lower()} for babies and kids',
                    'brand_keyword': brands[0].name if brands else None,
                    'price': Decimal('1000.00'),
                    'colors': ['Multi-color'],
                    'sizes': ['One Size']
                },
                {
                    'name': f'{category.name} Item 2',
                    'description': f'Premium {category.name.lower()} with excellent quality',
                    'brand_keyword': brands[1].name if len(brands) > 1 else brands[0].name if brands else None,
                    'price': Decimal('1500.00'),
                    'colors': ['White'],
                    'sizes': ['One Size']
                }
            ]
        
        # Create at least 2 products for each category
        products_to_create = matching_products[:2]  # Take first 2 products
        if len(products_to_create) < 2 and matching_products:
            # Duplicate if we have only one product
            products_to_create.append(matching_products[0])
        
        for i, product_data in enumerate(products_to_create):
            # Find brand
            brand = None
            if product_data.get('brand_keyword') and brands:
                brand = next((b for b in brands if b.name == product_data['brand_keyword']), brands[0])
            elif brands:
                brand = brands[i % len(brands)]
            
            # Find supplier
            supplier = suppliers[i % len(suppliers)] if suppliers else None
            
            # Create unique product name for category
            product_name = product_data['name']
            if i > 0:  # Add number to make it unique
                product_name = f"{product_data['name']} - Variant {i+1}"
            
            try:
                product = Product.objects.create(
                    name=product_name,
                    description=product_data['description'],
                    category=category,
                    brand=brand,
                    supplier=supplier,
                    price=product_data['price'],
                    sku=f"{category.name[:3].upper()}{Product.objects.count()+1:04d}",
                    is_active=True
                )
                
                # Create inventory for the product
                initial_stock = 50 + (i * 25)  # Varying stock levels
                Inventory.objects.create(
                    product=product,
                    quantity=initial_stock,
                    low_stock_threshold=10
                )
                
                created_products.append(product)
                print(f"Created product: {product.name} for category: {category.name}")
                
            except Exception as e:
                print(f"Error creating product {product_name}: {e}")
    
    return created_products


def main():
    """Main function to create all sample data"""
    print("Creating sample data for Baby and Kids Store...")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Create brands first
            print("\n1. Creating Brands...")
            brands = create_brands()
            
            # Create suppliers
            print("\n2. Creating Suppliers...")
            suppliers = create_suppliers()
            
            # Create colors and sizes
            print("\n3. Creating Colors and Sizes...")
            colors, sizes = create_colors_sizes()
            
            # Create products
            print("\n4. Creating Products...")
            products = create_sample_products()
            
            print("\n" + "=" * 50)
            print("SUMMARY:")
            print(f"✅ Brands created: {len(brands)}")
            print(f"✅ Suppliers created: {len(suppliers)}")
            print(f"✅ Colors created: {len(colors)}")
            print(f"✅ Sizes created: {len(sizes)}")
            print(f"✅ Products created: {len(products)}")
            
            # Final counts
            print(f"\nFinal database counts:")
            print(f"📊 Total Categories: {Category.objects.count()}")
            print(f"📊 Total Brands: {Brand.objects.count()}")
            print(f"📊 Total Suppliers: {Supplier.objects.count()}")
            print(f"📊 Total Products: {Product.objects.count()}")
            print(f"📊 Total Inventory Items: {Inventory.objects.count()}")
            
            print("\n🎉 Sample data creation completed successfully!")
            
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        raise


if __name__ == "__main__":
    main()