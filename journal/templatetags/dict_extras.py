from django import template

register = template.Library()

@register.filter
def get_by_key(dictionary, key):
    if dictionary is None:
        return {}
    return dictionary.get(key, {})