#!/usr/bin/env python3
"""
Script to add relevant images to all products in the inventory.
This script will create placeholder images and assign them to products based on their categories.
"""

import os
import sys
import django
from PIL import Image, ImageDraw, ImageFont
import random

# Set up Django environment
os.chdir('c:/Users/a2i/MyPy/Assignments/baby and kids')
sys.path.append('c:/Users/a2i/MyPy/Assignments/baby and kids')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kidstore.settings')
django.setup()

from inventory.models import Product, Category

def create_product_image(product_name, category_name, image_path):
    """Create a placeholder image for a product"""
    # Define colors for different categories
    category_colors = {
        'Aloms Panty Pant': '#FFB6C1',  # Light Pink
        'Aloms other pant': '#F0E68C',  # Khaki
        'Avaya': '#98FB98',  # Pale Green
        'Aveeno': '#87CEEB',  # Sky Blue
        'Boys Full Pant': '#4169E1',  # Royal Blue
        'Boys Half Pant': '#1E90FF',  # Dodger Blue
        'Boys Three Quarter Pant': '#6495ED',  # Cornflower Blue
        'Burka': '#DDA0DD',  # Plum
        'Cargo Pant': '#8FBC8F',  # Dark Sea Green
        'Cosmetics': '#FFB6C1',  # Light Pink
        'Export Jeans Half Pant': '#4682B4',  # Steel Blue
        'Export Jersey Half Pant': '#5F9EA0',  # Cadet Blue
        'Export Kneet Half Pant': '#708090',  # Slate Gray
        'Gevarding Pant': '#9370DB',  # Medium Purple
        'Jeans Full Pant': '#191970',  # Midnight Blue
        'Jeans Pant': '#000080',  # Navy
        'Johnson': '#FFE4B5',  # Moccasin
        'Kneet Pant': '#D2B48C',  # Tan
        'Kodomo': '#F5DEB3',  # Wheat
        'Long Tops Burka': '#E6E6FA',  # Lavender
        'Others': '#F0F8FF',  # Alice Blue
    }
    
    # Create image
    width, height = 400, 400
    color = category_colors.get(category_name, '#F0F0F0')  # Default light gray
    
    # Create image with solid background
    image = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(image)
    
    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Add category label at top
    draw.text((10, 10), category_name, fill='black', font=title_font)
    
    # Add product name (wrapped if too long)
    product_lines = []
    if len(product_name) > 30:
        words = product_name.split()
        current_line = ""
        for word in words:
            if len(current_line + word) < 30:
                current_line += word + " "
            else:
                if current_line:
                    product_lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            product_lines.append(current_line.strip())
    else:
        product_lines = [product_name]
    
    # Draw product name in center
    y_offset = height // 2 - (len(product_lines) * 25) // 2
    for i, line in enumerate(product_lines):
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y_offset + i * 25), line, fill='black', font=font)
    
    # Add some decorative elements based on category
    if 'Pant' in category_name or 'pant' in category_name:
        # Draw pants outline
        draw.rectangle([150, 250, 180, 350], outline='black', width=3)
        draw.rectangle([220, 250, 250, 350], outline='black', width=3)
        draw.line([150, 250, 250, 250], fill='black', width=3)
    elif 'Burka' in category_name:
        # Draw dress outline
        draw.polygon([(180, 280), (220, 280), (240, 350), (160, 350)], outline='black', width=3)
    elif 'Johnson' in category_name or 'Cosmetics' in category_name:
        # Draw bottle outline
        draw.rectangle([180, 280, 220, 350], outline='black', width=3)
        draw.rectangle([185, 270, 215, 285], outline='black', width=3)
    elif 'Others' in category_name:
        # Draw toy/gift box
        draw.rectangle([170, 290, 230, 340], outline='black', width=3)
        draw.line([170, 315, 230, 315], fill='black', width=2)
        draw.line([200, 290, 200, 340], fill='black', width=2)
    
    # Save image
    image.save(image_path, 'JPEG', quality=90)
    print(f"Created image: {image_path}")

def assign_images_to_products():
    """Assign images to all products that don't have them"""
    products_updated = 0
    
    # Create media directory if it doesn't exist
    media_dir = 'media/products'
    os.makedirs(media_dir, exist_ok=True)
    
    # Get all products without images
    products = Product.objects.filter(image='')
    
    print(f"Found {products.count()} products without images")
    
    for product in products:
        # Create filename based on product ID and name
        safe_name = "".join(c for c in product.name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')[:50]  # Limit length
        filename = f"product_{product.id}_{safe_name}.jpg"
        image_path = os.path.join(media_dir, filename)
        
        # Create the image
        create_product_image(product.name, product.category.name, image_path)
        
        # Update product with image path
        product.image = f'products/{filename}'
        product.save()
        
        products_updated += 1
        print(f"Updated product: {product.name}")
    
    return products_updated

def main():
    print("Starting product image assignment...")
    print("=" * 50)
    
    # Show current status
    total_products = Product.objects.count()
    products_without_images = Product.objects.filter(image='').count()
    
    print(f"Total products: {total_products}")
    print(f"Products without images: {products_without_images}")
    print()
    
    if products_without_images == 0:
        print("All products already have images!")
        return
    
    # Assign images
    updated_count = assign_images_to_products()
    
    print()
    print("=" * 50)
    print(f"Successfully updated {updated_count} products with images!")
    print("All products now have relevant placeholder images.")

if __name__ == "__main__":
    main()