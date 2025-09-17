from django import forms
from django.core.validators import RegexValidator
from .models import Customer, UserProfile

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone_number']
        labels = {
            'name': 'Customer Name',
            'email': 'Email Address (Optional)',
            'phone_number': 'Phone Number (Optional)'
        }
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'maxlength': '14',
                'type': 'text',
                'placeholder': '01xxxxxxxxx or +8801xxxxxxxxxx'
            })
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            return None
            
        # Remove spaces and dashes
        phone = phone.strip().replace(' ', '').replace('-', '')
        
        # If already properly formatted with country code
        if phone.startswith('+88') and len(phone) == 14:
            return phone
            
        # If 11 digits starting with 0
        if len(phone) == 11 and phone.startswith('0'):
            return f'+88{phone}'
            
        if phone:  # If there's any other format, raise error
            raise forms.ValidationError(
                "Phone number must be 11 digits starting with '0' (e.g., 01717508447) or include the country code (e.g., +8801717508447)"
            )
            
        return phone

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['is_salesperson']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.user.is_superuser:
            self.fields['is_salesperson'].disabled = True
