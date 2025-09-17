from django import template
from django.conf import settings
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def bdt(value):
    """
    Format a number as Bangladeshi Taka
    Example: 1234.56 -> ৳1,234.56
    """
    if value is None:
        return f"{settings.CURRENCY_SYMBOL}0.00"
    
    try:
        value = Decimal(str(value))
        formatted = "{:,.{}f}".format(value, settings.DEFAULT_DECIMAL_PLACES)
        return f"{settings.CURRENCY_SYMBOL}{formatted}"
    except (ValueError, TypeError, InvalidOperation):
        return f"{settings.CURRENCY_SYMBOL}0.00"
