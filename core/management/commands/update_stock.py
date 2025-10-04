from django.core.management.base import BaseCommand
from django.db import models
from inventory.models import Product, Inventory


class Command(BaseCommand):
    help = 'Update stock levels for all products to ensure minimum stock of 10 items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-stock',
            type=int,
            default=10,
            help='Minimum stock level to ensure (default: 10)',
        )
        parser.add_argument(
            '--set-to',
            type=int,
            default=15,
            help='Set stock to this level if below minimum (default: 15)',
        )

    def handle(self, *args, **options):
        min_stock = options['min_stock']
        set_to_stock = options['set_to']
        
        self.stdout.write("Updating Product Stock Levels...")
        self.stdout.write("=" * 50)
        
        # Get all products and their inventory
        products_updated = 0
        products_created = 0
        total_products = Product.objects.count()
        
        self.stdout.write(f"Checking {total_products} products...")
        self.stdout.write(f"Minimum stock level: {min_stock}")
        self.stdout.write(f"Update stock to: {set_to_stock}")
        self.stdout.write("")
        
        for product in Product.objects.all():
            try:
                # Get or create inventory for this product
                inventory, created = Inventory.objects.get_or_create(
                    product=product,
                    defaults={
                        'quantity': set_to_stock,
                        'low_stock_threshold': 5
                    }
                )
                
                if created:
                    self.stdout.write(f"Created inventory for {product.name}: {set_to_stock} units")
                    products_created += 1
                elif inventory.quantity < min_stock:
                    old_quantity = inventory.quantity
                    inventory.quantity = set_to_stock
                    inventory.save()
                    
                    self.stdout.write(f"Updated {product.name}: {old_quantity} → {inventory.quantity}")
                    products_updated += 1
                else:
                    self.stdout.write(f"OK: {product.name} - Current stock: {inventory.quantity}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error updating {product.name}: {e}")
                )
        
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write(
            self.style.SUCCESS(f"Stock Update Complete!")
        )
        self.stdout.write(f"✅ Products Updated: {products_updated}")
        self.stdout.write(f"✅ Inventories Created: {products_created}")
        self.stdout.write(f"✅ Products Already OK: {total_products - products_updated - products_created}")
        
        # Show summary statistics
        self.show_stock_summary(min_stock)

    def show_stock_summary(self, min_stock):
        """Show current stock summary"""
        
        self.stdout.write(f"\nStock Summary:")
        self.stdout.write("-" * 30)
        
        # Stock level categories
        very_low = Inventory.objects.filter(quantity__lt=5).count()
        low = Inventory.objects.filter(quantity__gte=5, quantity__lt=min_stock).count() 
        good = Inventory.objects.filter(quantity__gte=min_stock, quantity__lt=20).count()
        high = Inventory.objects.filter(quantity__gte=20).count()
        
        self.stdout.write(f"Very Low (< 5):       {very_low} products")
        self.stdout.write(f"Low (5-{min_stock-1}):           {low} products")
        self.stdout.write(f"Good ({min_stock}-19):        {good} products")
        self.stdout.write(f"High (20+):           {high} products")
        
        # Calculate average
        avg_stock = Inventory.objects.aggregate(
            avg_stock=models.Avg('quantity')
        )['avg_stock'] or 0
        
        self.stdout.write(f"\nAverage stock level: {avg_stock:.1f}")
        self.stdout.write(f"Total inventory items: {Inventory.objects.count()}")
        
        # Products that might need attention
        low_stock = Inventory.objects.select_related('product').filter(
            quantity__lt=min_stock
        ).order_by('quantity')
        
        if low_stock.exists():
            self.stdout.write(f"\n⚠️  Products Below {min_stock} Units:")
            for inv in low_stock:
                self.stdout.write(f"• {inv.product.name}: {inv.quantity} units")
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ All products have at least {min_stock} units in stock!")
            )