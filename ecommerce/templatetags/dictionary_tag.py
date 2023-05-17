from django import template

register = template.Library()

@register.filter
def iskey(value, arg):
    return value in arg
@register.filter
def get(value, arg):
    return value[arg]