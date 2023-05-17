from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from .models import *
from django.db.models import Sum
import json
from decimal import Decimal


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, customer, timestamp):
        return six.text_type(customer.pk) + six.text_type(timestamp) + six.text_type(customer.is_verify)


generate_token = TokenGenerator()


def product_qty(product):
    import_order_quantity = ImportOrderItem.objects.filter(product=product).aggregate(Sum('quantity'))[
                                'quantity__sum'] or 0
    purchase_order_quantity = PurchaseOrderItem.objects.filter(product=product).aggregate(Sum('quantity'))[
                                  'quantity__sum'] or 0

    product_quantity = import_order_quantity - purchase_order_quantity

    return product_quantity

class DecimalJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)