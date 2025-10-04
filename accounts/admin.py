from django.contrib import admin
from .models import Customer, UserProfile, ShopAssistant

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'total_purchase_value', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone_number')
    readonly_fields = ('total_purchase_value', 'created_at', 'updated_at')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_salesperson', 'phone_number')
    list_filter = ('is_salesperson',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')

@admin.register(ShopAssistant)
class ShopAssistantAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'joining_date', 'is_active', 'total_orders_display', 'total_sales_display')
    list_filter = ('is_active', 'joining_date')
    search_fields = ('name', 'contact_number')
    readonly_fields = ('total_orders_display', 'total_sales_display', 'created_at', 'updated_at')
    date_hierarchy = 'joining_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_number', 'joining_date', 'is_active')
        }),
        ('Additional Details', {
            'fields': ('address', 'notes'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('total_orders_display', 'total_sales_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_orders_display(self, obj):
        return obj.total_orders
    total_orders_display.short_description = 'Total Orders'
    
    def total_sales_display(self, obj):
        return f"৳{obj.total_sales:,.2f}"
    total_sales_display.short_description = 'Total Sales'
