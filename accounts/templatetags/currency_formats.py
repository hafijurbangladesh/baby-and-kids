from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter(name='bdt')
def format_bdt(value):
    """
    Format a number as BDT currency.
    Example: 1234.56 -> ৳1,234.56
    """
    if value is None:
        return '৳0.00'
    
    try:
        # Convert to float and format with 2 decimal places
        formatted_number = floatformat(float(value), 2)
        # Add thousand separators
        parts = str(formatted_number).split('.')
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else '00'
        
        # Add commas for thousands
        if len(integer_part) > 3:
            formatted_int = ''
            for i, digit in enumerate(reversed(integer_part)):
                if i > 0 and i % 3 == 0:
                    formatted_int = ',' + formatted_int
                formatted_int = digit + formatted_int
        else:
            formatted_int = integer_part
            
        # Combine with BDT symbol
        return f'৳{formatted_int}.{decimal_part}'
    except (ValueError, TypeError):
        return '৳0.00'
