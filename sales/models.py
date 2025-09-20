from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from inventory.models import Product

User = get_user_model()

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey('accounts.Customer', null=True, on_delete=models.PROTECT)
    salesperson = models.ForeignKey(User, on_delete=models.PROTECT)
    order_date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')

    def __str__(self):
        if self.customer:
            return f"Order #{self.id} - {self.customer.name}"
        return f"Order #{self.id} - Walk-in Customer"

    def calculate_totals(self):
        """Calculate order totals without saving"""
        if self.pk:  # Only calculate if order exists in database
            # Calculate subtotal by summing individual item totals with 2 decimal precision
            self.subtotal = sum(
                (item.price * item.quantity).quantize(Decimal('0.01'))
                for item in self.orderitem_set.all()
            )
            # Calculate tax with 2 decimal precision
            self.tax = (self.subtotal * Decimal('0.10')).quantize(Decimal('0.01'))  # 10% tax
            # Calculate total with 2 decimal precision
            self.total = (self.subtotal + self.tax).quantize(Decimal('0.01'))
        return self.subtotal, self.tax, self.total

    def save(self, *args, **kwargs):
        # Only auto-calculate totals if they're not set
        if not self.total and self.pk:
            self.calculate_totals()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

    @property
    def total(self):
        """Calculate and return the total for this order item"""
        return self.price * self.quantity

class Transaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
    ]

    order = models.OneToOneField(Order, on_delete=models.PROTECT)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction for Order #{self.order.id}"
