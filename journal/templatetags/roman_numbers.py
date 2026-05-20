from django import template

register = template.Library()

@register.filter
def to_roman(value):
    try:
        value = int(value)
        roman_map = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV',
            5: 'V', 6: 'VI', 7: 'VII'
        }
        return roman_map.get(value, str(value))
    except (ValueError, TypeError):
        return str(value)