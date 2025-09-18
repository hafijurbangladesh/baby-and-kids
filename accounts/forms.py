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
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'profile_picture', 'is_salesperson']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '01xxxxxxxxx or +8801xxxxxxxxx'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        # Apply Bootstrap classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
        
        # Disable is_salesperson field for non-superusers
        if not self.instance.user.is_superuser:
            self.fields['is_salesperson'].disabled = True

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update the User model fields
        if commit:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        
        return profile
