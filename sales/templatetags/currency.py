from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def taka(value):
    """Format a number as Bangladeshi Taka"""
    if value is None:
        return '৳0.00'
    try:
        value = Decimal(value)
        return f'৳{value:,.2f}'
    except:
        return '৳0.00'
