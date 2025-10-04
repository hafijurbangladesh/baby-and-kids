from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, Q, Avg
from decimal import Decimal

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=14, blank=True, null=True, 
                                  help_text="")
    total_purchase_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def calculate_total_purchase_value(self):
        """Calculate total purchase value from completed orders"""
        return self.order_set.filter(
            status='completed'
        ).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

    def update_total_purchase_value(self):
        """Update the total_purchase_value field with the calculated value"""
        self.total_purchase_value = self.calculate_total_purchase_value
        self.save(update_fields=['total_purchase_value'])

    def clean_phone_number(self):
        """Clean and format the phone number"""
        if not self.phone_number:
            return None

        # Remove any spaces and dashes
        phone = self.phone_number.strip().replace(' ', '').replace('-', '')
        
        # If already has +88 prefix, return as is
        if phone.startswith('+88') and len(phone) == 14:
            return phone
            
        # If it's an 11-digit number starting with 0
        if len(phone) == 11 and phone.startswith('0'):
            return f'+88{phone}'
            
        return phone

    def save(self, *args, **kwargs):
        """Override save to ensure phone number is properly formatted"""
        if self.phone_number:
            self.phone_number = self.clean_phone_number()
        
        # If this is a new customer, set initial total_purchase_value to 0
        if not self.id:
            self.total_purchase_value = Decimal('0.00')
        else:
            # Only calculate total_purchase_value for existing customers
            update_fields = kwargs.get('update_fields', None)
            if update_fields and 'total_purchase_value' not in update_fields:
                self.total_purchase_value = self.calculate_total_purchase_value
        
        super().save(*args, **kwargs)

    def get_formatted_phone(self):
        """Get the formatted phone number for display"""
        if not self.phone_number:
            return "Not provided"
        return self.phone_number

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=14, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_salesperson = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"

    def clean_phone_number(self):
        """Clean and format the phone number"""
        if not self.phone_number:
            return None

        # Remove any spaces and dashes
        phone = self.phone_number.strip().replace(' ', '').replace('-', '')
        
        # If already has +88 prefix, return as is
        if phone.startswith('+88') and len(phone) == 14:
            return phone
            
        # If it's an 11-digit number starting with 0
        if len(phone) == 11 and phone.startswith('0'):
            return f'+88{phone}'
            
        return phone

    def save(self, *args, **kwargs):
        """Override save to ensure phone number is properly formatted"""
        if self.phone_number:
            self.phone_number = self.clean_phone_number()
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class ShopAssistant(models.Model):
    """Model for shop assistants (non-system users who assist in sales)"""
    name = models.CharField(max_length=100, help_text="Full name of the shop assistant")
    contact_number = models.CharField(
        max_length=14, 
        blank=True, 
        null=True,
        help_text="Contact number in format +8801XXXXXXXXX"
    )
    joining_date = models.DateField(help_text="Date when the assistant joined")
    is_active = models.BooleanField(default=True, help_text="Whether the assistant is currently active")
    address = models.TextField(blank=True, null=True, help_text="Home address of the assistant")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or comments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Shop Assistant'
        verbose_name_plural = 'Shop Assistants'

    def __str__(self):
        return self.name

    def clean_phone_number(self):
        """Clean and format the phone number"""
        if not self.contact_number:
            return None

        # Remove any spaces and dashes
        phone = self.contact_number.strip().replace(' ', '').replace('-', '')
        
        # If already has +88 prefix, return as is
        if phone.startswith('+88') and len(phone) == 14:
            return phone
            
        # If it's an 11-digit number starting with 0
        if len(phone) == 11 and phone.startswith('0'):
            return f'+88{phone}'
            
        return phone

    def save(self, *args, **kwargs):
        """Override save to ensure phone number is properly formatted"""
        if self.contact_number:
            self.contact_number = self.clean_phone_number()
        super().save(*args, **kwargs)

    def get_formatted_phone(self):
        """Get the formatted phone number for display"""
        if not self.contact_number:
            return "Not provided"
        return self.contact_number

    @property
    def total_sales(self):
        """Calculate total sales amount assisted by this shop assistant"""
        from sales.models import Order
        from django.db.models import Sum
        result = Order.objects.filter(
            shop_assistant=self,
            status='completed'
        ).aggregate(total=Sum('total'))['total']
        return result or Decimal('0.00')

    @property
    def total_orders(self):
        """Calculate total number of orders assisted by this shop assistant"""
        from sales.models import Order
        return Order.objects.filter(
            shop_assistant=self,
            status='completed'
        ).count()

    def get_performance_data(self, start_date=None, end_date=None):
        """Get performance data for a specific date range"""
        from sales.models import Order
        from django.db.models import Sum, Avg
        from django.utils import timezone
        
        queryset = Order.objects.filter(
            shop_assistant=self,
            status='completed'
        )
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
            
        total_sales = queryset.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        total_orders = queryset.count()
        avg_order_value = queryset.aggregate(avg=Avg('total'))['avg'] or Decimal('0.00')
        
        # Calculate performance percentage (relative to best performer)
        max_sales = Decimal('10000')  # Assuming max target of 10,000 per period
        performance_percentage = min(Decimal('100'), (total_sales / max_sales * Decimal('100')) if max_sales > 0 else Decimal('0'))
            
        return {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
            'performance_percentage': performance_percentage,
        }
