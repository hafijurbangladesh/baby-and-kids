from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, Q
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
