from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

class Command(BaseCommand):
    help = 'Clean up system data while preserving users, shop assistants, and customers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete the data (required for safety)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete:\n'
                    '- All sales orders and transactions\n'
                    '- All inventory and product data\n'
                    '- All stock adjustments\n\n'
                    'The following will be PRESERVED:\n'
                    '- System users (admin, staff)\n'
                    '- Shop assistants\n'
                    '- Customer data\n\n'
                    'To confirm, run: python manage.py cleanup_data --confirm'
                )
            )
            return

        self.stdout.write('Starting data cleanup...')
        
        try:
            with transaction.atomic():
                deleted_counts = self.cleanup_data()
                
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nData cleanup completed successfully!\n\n'
                    f'Deleted:\n'
                    f'- Orders: {deleted_counts["orders"]}\n'
                    f'- Order Items: {deleted_counts["order_items"]}\n'
                    f'- Transactions: {deleted_counts["transactions"]}\n'
                    f'- Products: {deleted_counts["products"]}\n'
                    f'- Inventory Records: {deleted_counts["inventory"]}\n'
                    f'- Stock Adjustments: {deleted_counts["stock_adjustments"]}\n'
                    f'- Categories: {deleted_counts["categories"]}\n'
                    f'- Brands: {deleted_counts["brands"]}\n'
                    f'- Colors: {deleted_counts["colors"]}\n'
                    f'- Sizes: {deleted_counts["sizes"]}\n'
                    f'- Suppliers: {deleted_counts["suppliers"]}\n\n'
                    f'Preserved:\n'
                    f'- System users: ✓\n'
                    f'- Shop assistants: ✓\n'
                    f'- Customers: ✓'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
            raise

    def cleanup_data(self):
        """Clean up data and return counts of deleted items"""
        
        # Import models
        from sales.models import Order, OrderItem, Transaction
        from inventory.models import (
            Product, Inventory, StockAdjustment, 
            Category, Brand, Color, Size, Supplier
        )
        
        deleted_counts = {}
        
        # 1. Delete sales-related data (transactions must be deleted before orders due to protected FK)
        self.stdout.write('Deleting sales data...')
        deleted_counts['transactions'] = Transaction.objects.count()
        Transaction.objects.all().delete()
        
        deleted_counts['order_items'] = OrderItem.objects.count()
        OrderItem.objects.all().delete()
        
        deleted_counts['orders'] = Order.objects.count()  
        Order.objects.all().delete()
        
        # 2. Delete inventory and product data
        self.stdout.write('Deleting inventory data...')
        deleted_counts['stock_adjustments'] = StockAdjustment.objects.count()
        StockAdjustment.objects.all().delete()
        
        deleted_counts['inventory'] = Inventory.objects.count()
        Inventory.objects.all().delete()
        
        deleted_counts['products'] = Product.objects.count()
        Product.objects.all().delete()
        
        # 3. Delete product attributes (these might be referenced by products)
        self.stdout.write('Deleting product attributes...')
        deleted_counts['categories'] = Category.objects.count()
        Category.objects.all().delete()
        
        deleted_counts['brands'] = Brand.objects.count()
        Brand.objects.all().delete()
        
        deleted_counts['colors'] = Color.objects.count()
        Color.objects.all().delete()
        
        deleted_counts['sizes'] = Size.objects.count()
        Size.objects.all().delete()
        
        deleted_counts['suppliers'] = Supplier.objects.count()
        Supplier.objects.all().delete()
        
        # Note: We're NOT deleting:
        # - User objects (system users)
        # - ShopAssistant objects
        # - Customer objects
        # - UserProfile objects
        
        return deleted_counts

    def get_confirmation(self):
        """Get user confirmation for the cleanup"""
        response = input('Are you sure you want to proceed? Type "yes" to confirm: ')
        return response.lower() == 'yes'