from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from accounts.models import Customer
from inventory.models import Product, Category, Inventory
from sales.models import Order, OrderItem
from decimal import Decimal
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generates dummy data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating dummy data...')
        
        # Create test user if not exists
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'is_staff': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created test user: testuser (password: testpass123)')

        # Create categories
        categories = [
            'Baby Clothes',
            'Toys',
            'Diapers',
            'Feeding',
            'Strollers',
            'Car Seats',
            'Baby Care',
            'Nursery'
        ]
        
        for cat_name in categories:
            Category.objects.get_or_create(name=cat_name)
        
        self.stdout.write(f'Created {len(categories)} categories')

        # Create products with inventory (prices in BDT)
        products_data = [
            ('Baby Onesie', 'Baby Clothes', 799.00, 50),
            ('Wooden Blocks Set', 'Toys', 1299.00, 30),
            ('Premium Diapers Pack', 'Diapers', 1899.00, 100),
            ('Baby Bottle Set', 'Feeding', 1499.00, 40),
            ('Lightweight Stroller', 'Strollers', 12999.00, 10),
            ('Infant Car Seat', 'Car Seats', 15999.00, 15),
            ('Baby Lotion', 'Baby Care', 599.00, 60),
            ('Baby Crib', 'Nursery', 24999.00, 8),
            ('Baby Blanket', 'Nursery', 1299.00, 45),
            ('Teething Toy', 'Toys', 399.00, 75)
        ]

        for name, category, price, stock in products_data:
            category_obj = Category.objects.get(name=category)
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': category_obj,
                    'price': price,
                    'description': f'Test {name} for babies',
                }
            )
            
            if created:
                Inventory.objects.create(
                    product=product,
                    quantity=stock,
                    low_stock_threshold=5
                )

        self.stdout.write(f'Created {len(products_data)} products with inventory')

        # Create customers
        customer_names = [
            'John Smith',
            'Mary Johnson',
            'David Brown',
            'Sarah Wilson',
            'Michael Davis'
        ]

        customers = []
        for name in customer_names:
            customer, created = Customer.objects.get_or_create(
                name=name,
                defaults={
                    'email': f'{name.lower().replace(" ", ".")}@example.com',
                    'phone': f'09{random.randint(100000000, 999999999)}'
                }
            )
            customers.append(customer)

        self.stdout.write(f'Created {len(customers)} customers')

        # Create orders for the last 30 days
        today = timezone.now()
        products = list(Product.objects.all())
        
        for i in range(50):  # Create 50 orders
            order_date = today - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            customer = random.choice(customers)
            order = Order.objects.create(
                customer=customer,
                salesperson=user,
                order_date=order_date,
                status='completed'
            )

            # Add 1-5 products to each order
            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )

            # Update order total
            order.total = sum(item.quantity * item.price for item in order.items.all())
            order.save()

            # Update inventory
            for item in order.items.all():
                inventory = item.product.inventory
                inventory.quantity = max(0, inventory.quantity - item.quantity)
                inventory.save()

        self.stdout.write(f'Created 50 orders with items')
        self.stdout.write(self.style.SUCCESS('Successfully created dummy data'))
