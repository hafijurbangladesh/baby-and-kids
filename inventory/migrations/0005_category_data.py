from django.db import migrations

def create_categories(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    
    # Clear existing categories
    Category.objects.all().delete()
    
    # Create main categories
    categories = {
        'Newborn Essentials': {
            'Bodysuits & Onesies': {
                'Short Sleeve': {},
                'Long Sleeve': {},
                'Sleeveless': {},
            },
            'Sleepwear': {
                'Sleepsuits': {},
                'Swaddles': {},
                'Sleeping Bags': {},
            },
            'Sets & Gift Packs': {
                'Hospital Coming-Home Sets': {},
                'Baby Shower Packs': {},
            },
        },
        'Tops & Bottoms': {
            'Tops': {
                'T-Shirts': {},
                'Shirts': {},
                'Sweaters': {},
            },
            'Bottoms': {
                'Leggings': {},
                'Pants': {},
                'Shorts': {},
                'Skirts': {},
            },
        },
        'Outerwear': {
            'Jackets & Coats': {
                'Hooded Jackets': {},
                'Puffer Jackets': {},
                'Raincoats': {},
            },
            'Sweaters & Cardigans': {},
            'Vests': {},
        },
        'Dresses & Rompers': {
            'Dresses': {
                'Casual Dresses': {},
                'Party Dresses': {},
                'Christening Dresses': {},
            },
            'Rompers & Jumpsuits': {
                'Short Rompers': {},
                'Long Rompers': {},
            },
        },
        'Special Occasion Wear': {
            'Festive Wear': {
                'Eid/Christmas Outfits': {},
                'Birthday Outfits': {},
            },
            'Formal Wear': {
                'Suits & Blazers': {},
                'Dress Gowns': {},
            },
        },
        'Sleep & Loungewear': {
            'Pajamas': {
                'Two-Piece Pajamas': {},
                'One-Piece Pajamas': {},
                'Nightgowns': {},
            },
            'Loungewear Sets': {},
        },
        'Accessories': {
            'Headwear': {
                'Hats': {},
                'Beanies': {},
                'Headbands': {},
            },
            'Footwear': {
                'Booties': {},
                'Sandals': {},
                'Socks': {},
            },
            'Gloves & Mittens': {},
            'Bibs & Burp Cloths': {},
        },
        'Seasonal Wear': {
            'Summer': {
                'Swimsuits': {},
                'Sun Hats': {},
            },
            'Winter': {
                'Thermal Wear': {},
                'Wool Caps & Scarves': {},
            },
        },
    }

    def create_category_tree(data, parent=None):
        for name, children in data.items():
            category = Category.objects.create(
                name=name,
                parent=parent,
                description=f"Category for {name}"
            )
            if children:
                create_category_tree(children, category)

    create_category_tree(categories)

def reverse_categories(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    Category.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0004_alter_category_options_category_created_at_and_more'),
    ]

    operations = [
        migrations.RunPython(create_categories, reverse_categories),
    ]
