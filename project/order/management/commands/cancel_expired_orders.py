from datetime import datetime
from django.core.management.base import BaseCommand

from order.models import Order
from order.utils import cancel_order


class Command(BaseCommand):
    help = 'Get tickets for a given range'

    def handle(self, *args, **kwargs):
        for order in Order.objects.expired_orders():
            cancel_order(
                client=order.payer,
                caster=0,
                order_pk=order.pk,
                type=6
            )

