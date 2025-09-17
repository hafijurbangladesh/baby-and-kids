from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db import transaction
from accounts.models import Customer
from sales.models import Order

class Command(BaseCommand):
    help = 'Recalculate total purchase values for all customers'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            # Get all customers
            customers = Customer.objects.all()
            total_updated = 0

            for customer in customers:
                # Calculate total from completed orders only
                total = Order.objects.filter(
                    customer=customer,
                    status='completed'
                ).aggregate(
                    total=Sum('total')
                )['total'] or 0

                # Update customer if total is different
                if customer.total_purchase_value != total:
                    customer.total_purchase_value = total
                    customer.save(update_fields=['total_purchase_value'])
                    total_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {total_updated} customers\' total purchase values'
                )
            )
