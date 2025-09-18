from django.db import migrations

def create_categories(apps, schema_editor):
    Category = apps.get_model('inventory', 'Category')
    
    def create_category_tree(name, parent=None):
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={'parent': parent}
        )
        return category
    
    # Get or create categories
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

    def process_categories(data, parent=None):
        for name, children in data.items():
            category = create_category_tree(name, parent)
            if children:
                process_categories(children, category)

    process_categories(categories)

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
