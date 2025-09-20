from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='bdt')
def format_bdt(value):
    """Format a number as Bangladeshi Taka"""
    if value is None:
        return '৳0.00'
    try:
        value = float(value)
        return f'৳{value:,.2f}'
    except (ValueError, TypeError):
        return value
