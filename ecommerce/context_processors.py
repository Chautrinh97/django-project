from .models import *
from django.db.models import Count
def menu(request):
    # header
    try:
        customer = Customer.objects.get(id=request.session.get('customer'))
    except:
        customer = None
    brands = Brand.objects.annotate(num_products=Count('product')).order_by('-num_products')[:8]
    types = InstrumentType.objects.all()
    types_categories = {}
    for type in types:
        categories = type.category_set.all()
        types_categories[type] = categories
    context = {
        'customer':customer,
        'all_brands': brands,
        'all_types_categories': types_categories,
    }
    return context

def cart(request):
    context = {}
    if 'cart' in request.session:
        cart = list(request.session['cart'].items())
        minicart = cart[-3:] if len(cart)>3 else cart
        context = {'minicart': dict(minicart), 'num_in_cart':len(cart)}
    return context