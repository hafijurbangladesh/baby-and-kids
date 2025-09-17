from django.contrib import admin
from .models import Category, Brand, Supplier, Product, Inventory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'contact_info')
    search_fields = ('name', 'contact_person')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'category', 'brand', 'supplier')
    list_filter = ('category', 'brand', 'supplier')
    search_fields = ('name', 'sku')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'low_stock_threshold')
    list_filter = ('product__category', 'product__brand')
    search_fields = ('product__name', 'product__sku')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')
