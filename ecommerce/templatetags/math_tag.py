from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    return value * arg

@register.filter
def add(value, arg):
    return value + arg

@register.filter
def total(value):
    total = 0
    for key, data in value.items():
        total+=data['quantity']*data['price']
    return total