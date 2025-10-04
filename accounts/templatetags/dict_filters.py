from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def get_attr(obj, attr_name):
    """Get an attribute from an object"""
    try:
        return getattr(obj, attr_name, None)
    except:
        return None