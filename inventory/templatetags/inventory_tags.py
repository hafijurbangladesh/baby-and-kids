from django import template
from django.db.models import QuerySet

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_attr(queryset, attr_name):
    """Sum a specific attribute across all objects in a queryset"""
    if not isinstance(queryset, QuerySet):
        return 0
    try:
        total = 0
        for obj in queryset:
            value = getattr(obj, attr_name, 0)
            if value is not None:
                total += float(value)
        return total
    except (ValueError, TypeError, AttributeError):
        return 0
