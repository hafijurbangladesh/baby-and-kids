from django import forms
from .models import Product, Inventory

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'brand', 
                 'supplier', 'image', 'sku', 'color', 'size']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'})
        }

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if self.instance.pk:  # If editing existing product
            exists = Product.objects.exclude(pk=self.instance.pk).filter(sku=sku).exists()
        else:  # If creating new product
            exists = Product.objects.filter(sku=sku).exists()
        if exists:
            raise forms.ValidationError('A product with this SKU already exists.')
        return sku

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['quantity', 'low_stock_threshold']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '0'}),
            'low_stock_threshold': forms.NumberInput(attrs={'min': '1'})
        }


class StockAdjustmentForm(forms.Form):
    adjustment = forms.IntegerField(
        label='Stock Adjustment',
        help_text='Use positive numbers to add stock, negative to remove.'
    )
    reason = forms.CharField(
        label='Reason for Adjustment',
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Please provide a reason for this stock adjustment.'
    )
