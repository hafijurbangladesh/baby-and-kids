from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import Category, Brand, Supplier, Product, Inventory
from decimal import Decimal

class Command(BaseCommand):
    help = 'Add sample data to the database'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Adding sample data...')

        # Create Categories
        categories = [
            {'name': 'Clothing', 'description': 'Baby and kids clothing items'},
            {'name': 'Toys', 'description': 'Educational and fun toys'},
            {'name': 'Accessories', 'description': 'Various baby and kids accessories'},
            {'name': 'School Supplies', 'description': 'Items for school and learning'},
            {'name': 'Baby Care', 'description': 'Essential baby care products'}
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(**cat_data)
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create Brands
        brands = [
            {'name': 'KidsWear'},
            {'name': 'ToyMaster'},
            {'name': 'BabyEssentials'},
            {'name': 'SchoolTime'},
            {'name': 'LittleComfort'}
        ]
        
        for brand_data in brands:
            brand, created = Brand.objects.get_or_create(**brand_data)
            if created:
                self.stdout.write(f'Created brand: {brand.name}')

        # Create Suppliers
        suppliers = [
            {
                'name': 'Kids Wholesale Co.',
                'contact_person': 'John Smith',
                'contact_info': 'john@kidswholesale.com'
            },
            {
                'name': 'Baby Products Supply',
                'contact_person': 'Mary Johnson',
                'contact_info': 'mary@babyproducts.com'
            },
            {
                'name': 'Toy Distributors',
                'contact_person': 'David Wilson',
                'contact_info': 'david@toydist.com'
            }
        ]
        
        for supplier_data in suppliers:
            supplier, created = Supplier.objects.get_or_create(**supplier_data)
            if created:
                self.stdout.write(f'Created supplier: {supplier.name}')

        # Create Products and Inventory
        products = [
            {
                'name': 'Baby T-Shirt',
                'description': 'Comfortable cotton t-shirt for babies',
                'price': Decimal('19.99'),
                'category': Category.objects.get(name='Clothing'),
                'brand': Brand.objects.get(name='KidsWear'),
                'supplier': Supplier.objects.get(name='Kids Wholesale Co.'),
                'sku': 'BTS001',
                'inventory_data': {'quantity': 50, 'low_stock_threshold': 10}
            },
            {
                'name': 'Educational Building Blocks',
                'description': 'Colorful building blocks for learning',
                'price': Decimal('29.99'),
                'category': Category.objects.get(name='Toys'),
                'brand': Brand.objects.get(name='ToyMaster'),
                'supplier': Supplier.objects.get(name='Toy Distributors'),
                'sku': 'TBB001',
                'inventory_data': {'quantity': 30, 'low_stock_threshold': 5}
            },
            {
                'name': 'School Backpack',
                'description': 'Durable backpack for school',
                'price': Decimal('34.99'),
                'category': Category.objects.get(name='School Supplies'),
                'brand': Brand.objects.get(name='SchoolTime'),
                'supplier': Supplier.objects.get(name='Kids Wholesale Co.'),
                'sku': 'SBP001',
                'inventory_data': {'quantity': 25, 'low_stock_threshold': 5}
            },
            {
                'name': 'Baby Lotion',
                'description': 'Gentle moisturizing lotion for babies',
                'price': Decimal('12.99'),
                'category': Category.objects.get(name='Baby Care'),
                'brand': Brand.objects.get(name='BabyEssentials'),
                'supplier': Supplier.objects.get(name='Baby Products Supply'),
                'sku': 'BCL001',
                'inventory_data': {'quantity': 40, 'low_stock_threshold': 8}
            },
            {
                'name': 'Kids Hair Accessories Set',
                'description': 'Colorful hair clips and bands',
                'price': Decimal('9.99'),
                'category': Category.objects.get(name='Accessories'),
                'brand': Brand.objects.get(name='LittleComfort'),
                'supplier': Supplier.objects.get(name='Kids Wholesale Co.'),
                'sku': 'AHA001',
                'inventory_data': {'quantity': 60, 'low_stock_threshold': 15}
            }
        ]
        
        for product_data in products:
            inventory_data = product_data.pop('inventory_data')
            product, created = Product.objects.get_or_create(**product_data)
            if created:
                self.stdout.write(f'Created product: {product.name}')
                inventory = Inventory.objects.create(
                    product=product,
                    **inventory_data
                )
                self.stdout.write(f'Created inventory for: {product.name}')

        self.stdout.write(self.style.SUCCESS('Successfully added sample data'))
