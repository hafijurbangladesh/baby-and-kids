from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent} >> {self.name}"
        return self.name

    def get_hierarchy(self):
        if self.parent:
            return f"{self.parent.get_hierarchy()} >> {self.name}"
        return self.name

    def get_children(self):
        return self.children.all()

    def has_children(self):
        return self.children.exists()

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

class Brand(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    contact_info = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField()

    def __str__(self):
        return f"{self.product.name} - Qty: {self.quantity}"

    class Meta:
        verbose_name_plural = "Inventories"


class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = [
        ('addition', 'Stock Addition'),
        ('reduction', 'Stock Reduction'),
        ('correction', 'Stock Correction'),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_adjustments')
    quantity = models.IntegerField(help_text="Use positive numbers for additions, negative for reductions")
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    reason = models.TextField()
    adjusted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        action = "added to" if self.quantity > 0 else "removed from"
        return f"{abs(self.quantity)} items {action} {self.product.name}"
