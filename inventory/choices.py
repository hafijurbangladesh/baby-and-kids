from django.db import models
from django.core.management import call_command
from .models import Color, Size

def populate_default_colors():
    default_colors = [
        'Red', 'Blue', 'Green', 'Yellow', 'Black', 'White', 'Pink', 
        'Purple', 'Orange', 'Grey', 'Navy', 'Brown', 'Multi'
    ]
    for color in default_colors:
        Color.objects.get_or_create(name=color)

def populate_default_sizes():
    default_sizes = [
        'Newborn', '0-3M', '3-6M', '6-9M', '9-12M', '12-18M', '18-24M',
        '2Y', '3Y', '4Y', '5Y', '6Y', '7Y', '8Y', '9Y', '10Y',
        'XS', 'S', 'M', 'L', 'XL'
    ]
    for size in default_sizes:
        Size.objects.get_or_create(name=size)
