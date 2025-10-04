#!/usr/bin/env python
"""
Fix user permissions for inventory management
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from inventory.models import Inventory, Product

def fix_permissions():
    """Grant inventory permissions to all staff users"""
    
    print("FIXING INVENTORY PERMISSIONS")
    print("=" * 50)
    
    # Get inventory related permissions
    inventory_ct = ContentType.objects.get_for_model(Inventory)
    product_ct = ContentType.objects.get_for_model(Product)
    
    # Get or create required permissions
    inventory_permissions = [
        Permission.objects.get_or_create(
            codename='change_inventory',
            name='Can change inventory',
            content_type=inventory_ct
        )[0],
        Permission.objects.get_or_create(
            codename='view_inventory', 
            name='Can view inventory',
            content_type=inventory_ct
        )[0],
        Permission.objects.get_or_create(
            codename='add_inventory',
            name='Can add inventory', 
            content_type=inventory_ct
        )[0]
    ]
    
    product_permissions = [
        Permission.objects.get_or_create(
            codename='change_product',
            name='Can change product',
            content_type=product_ct
        )[0],
        Permission.objects.get_or_create(
            codename='view_product',
            name='Can view product', 
            content_type=product_ct
        )[0]
    ]
    
    # Get all staff users
    staff_users = User.objects.filter(is_staff=True)
    
    print(f"Found {staff_users.count()} staff users:")
    
    for user in staff_users:
        print(f"\n👤 {user.username} ({'Superuser' if user.is_superuser else 'Staff'})")
        
        if not user.is_superuser:
            # Add inventory permissions
            for perm in inventory_permissions:
                user.user_permissions.add(perm)
                print(f"  ✅ Added: {perm.name}")
            
            # Add product permissions  
            for perm in product_permissions:
                user.user_permissions.add(perm)
                print(f"  ✅ Added: {perm.name}")
        else:
            print(f"  ℹ️  Superuser already has all permissions")
    
    print(f"\n✅ Permissions updated for {staff_users.count()} staff users")

if __name__ == "__main__":
    fix_permissions()